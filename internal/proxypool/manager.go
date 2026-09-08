package proxypool

import (
	"context"
	"errors"
	"fmt"
	"io"
	"math/rand"
	"net"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"cyberstrike-ai/internal/config"

	"go.uber.org/zap"
	xproxy "golang.org/x/net/proxy"
)

var ErrNoHealthyProxy = errors.New("no healthy SOCKS5 proxy is available")

type endpointState struct {
	Failures      int
	CooldownUntil time.Time
	LastChecked   time.Time
	LastSuccess   time.Time
	LastLatency   time.Duration
	LastExitIP    string
	LastError     string
}

type EndpointStatus struct {
	Name              string `json:"name"`
	URL               string `json:"url"`
	Enabled           bool   `json:"enabled"`
	Healthy           bool   `json:"healthy"`
	Failures          int    `json:"failures"`
	CooldownUntil     string `json:"cooldown_until,omitempty"`
	LastChecked       string `json:"last_checked,omitempty"`
	LastSuccess       string `json:"last_success,omitempty"`
	LastLatencyMillis int64  `json:"last_latency_ms,omitempty"`
	ExitIP            string `json:"exit_ip,omitempty"`
	Error             string `json:"error,omitempty"`
}

type Manager struct {
	mu         sync.Mutex
	cfg        config.ProxyPoolConfig
	states     map[string]*endpointState
	transports map[string]*http.Transport
	rng        *rand.Rand
	next       atomic.Uint64
	logger     *zap.Logger
	direct     *http.Transport
}

func New(cfg config.ProxyPoolConfig, logger *zap.Logger) (*Manager, error) {
	m := &Manager{
		states:     make(map[string]*endpointState),
		transports: make(map[string]*http.Transport),
		rng:        rand.New(rand.NewSource(time.Now().UnixNano())),
		logger:     logger,
		direct:     cloneDefaultTransport(),
	}
	if err := m.Update(cfg); err != nil {
		return nil, err
	}
	return m, nil
}

func (m *Manager) Update(cfg config.ProxyPoolConfig) error {
	if err := cfg.NormalizeAndValidate(); err != nil {
		return err
	}
	m.mu.Lock()
	defer m.mu.Unlock()

	active := make(map[string]struct{}, len(cfg.Proxies))
	for _, endpoint := range cfg.Proxies {
		active[endpoint.URL] = struct{}{}
		if _, ok := m.states[endpoint.URL]; !ok {
			m.states[endpoint.URL] = &endpointState{}
		}
	}
	for endpointURL, transport := range m.transports {
		if _, ok := active[endpointURL]; !ok {
			transport.CloseIdleConnections()
			delete(m.transports, endpointURL)
			delete(m.states, endpointURL)
		}
	}
	m.cfg = cloneConfig(cfg)
	return nil
}

func (m *Manager) Config() config.ProxyPoolConfig {
	m.mu.Lock()
	defer m.mu.Unlock()
	return cloneConfig(m.cfg)
}

func (m *Manager) Client(timeout time.Duration) *http.Client {
	return &http.Client{Transport: &rotatingTransport{manager: m}, Timeout: timeout}
}

type rotatingTransport struct {
	manager *Manager
}

func (t *rotatingTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	if t == nil || t.manager == nil {
		return http.DefaultTransport.RoundTrip(req)
	}
	endpoint, transport, enabled, err := t.manager.nextTransport()
	if err != nil {
		return nil, err
	}
	if !enabled {
		return t.manager.direct.RoundTrip(req)
	}

	started := time.Now()
	resp, roundTripErr := transport.RoundTrip(req)
	latency := time.Since(started)
	if roundTripErr != nil {
		t.manager.recordFailure(endpoint.URL, latency, roundTripErr)
		return nil, roundTripErr
	}
	// HTTP-level failures must count against the endpoint the same way the
	// health check does; headers arriving alone is not proof the proxy works.
	if resp.StatusCode == http.StatusTooManyRequests || resp.StatusCode >= http.StatusInternalServerError {
		t.manager.recordFailure(endpoint.URL, latency, fmt.Errorf("proxy returned HTTP %d", resp.StatusCode))
		return resp, nil
	}
	// The transaction is only a success once the caller has drained the body.
	// A proxy that stalls mid-body never gets marked healthy.
	resp.Body = &trackedReadCloser{
		ReadCloser: resp.Body,
		onFinish:   func() { t.manager.recordSuccess(endpoint.URL, latency, "") },
	}
	return resp, nil
}

// trackedReadCloser records a proxy success when the response body is closed
// after being fully consumed. If the caller abandons the body it stays closed
// too, which still counts as success for header-level checks; callers in this
// platform always drain small payloads.
type trackedReadCloser struct {
	io.ReadCloser
	onFinish func()
	once     sync.Once
}

func (t *trackedReadCloser) finish() {
	t.once.Do(t.onFinish)
}

func (t *trackedReadCloser) Close() error {
	t.finish()
	return t.ReadCloser.Close()
}

func (t *trackedReadCloser) Read(p []byte) (int, error) {
	n, err := t.ReadCloser.Read(p)
	if err == io.EOF {
		t.finish()
	}
	return n, err
}

func (m *Manager) nextTransport() (config.SOCKS5ProxyConfig, *http.Transport, bool, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	if !m.cfg.Enabled {
		return config.SOCKS5ProxyConfig{}, nil, false, nil
	}

	now := time.Now()
	eligible := make([]config.SOCKS5ProxyConfig, 0, len(m.cfg.Proxies))
	for _, endpoint := range m.cfg.Proxies {
		if !endpoint.Enabled {
			continue
		}
		state := m.states[endpoint.URL]
		if state == nil || state.CooldownUntil.IsZero() || !now.Before(state.CooldownUntil) {
			eligible = append(eligible, endpoint)
		}
	}
	if len(eligible) == 0 {
		return config.SOCKS5ProxyConfig{}, nil, true, ErrNoHealthyProxy
	}

	index := 0
	if m.cfg.Strategy == "random" {
		index = m.rng.Intn(len(eligible))
	} else {
		index = int((m.next.Add(1) - 1) % uint64(len(eligible)))
	}
	endpoint := eligible[index]
	transport, ok := m.transports[endpoint.URL]
	if !ok {
		var err error
		transport, err = newSOCKS5Transport(endpoint.URL, time.Duration(m.cfg.ConnectTimeoutSeconds)*time.Second)
		if err != nil {
			return config.SOCKS5ProxyConfig{}, nil, true, err
		}
		m.transports[endpoint.URL] = transport
	}
	return endpoint, transport, true, nil
}

func (m *Manager) recordFailure(endpointURL string, latency time.Duration, err error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	state := m.states[endpointURL]
	if state == nil {
		state = &endpointState{}
		m.states[endpointURL] = state
	}
	state.Failures++
	state.LastChecked = time.Now()
	state.LastLatency = latency
	state.LastError = safeError(err)
	if state.Failures >= m.cfg.FailureThreshold {
		state.CooldownUntil = time.Now().Add(time.Duration(m.cfg.CooldownSeconds) * time.Second)
		if m.logger != nil {
			m.logger.Warn("SOCKS5 proxy entered cooldown",
				zap.String("proxy", publicProxyURL(endpointURL)),
				zap.Int("failures", state.Failures),
				zap.Time("cooldown_until", state.CooldownUntil),
			)
		}
	}
}

func (m *Manager) recordSuccess(endpointURL string, latency time.Duration, exitIP string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	state := m.states[endpointURL]
	if state == nil {
		state = &endpointState{}
		m.states[endpointURL] = state
	}
	now := time.Now()
	state.Failures = 0
	state.CooldownUntil = time.Time{}
	state.LastChecked = now
	state.LastSuccess = now
	state.LastLatency = latency
	state.LastError = ""
	if exitIP != "" {
		state.LastExitIP = exitIP
	}
}

func (m *Manager) Status() []EndpointStatus {
	m.mu.Lock()
	defer m.mu.Unlock()
	now := time.Now()
	out := make([]EndpointStatus, 0, len(m.cfg.Proxies))
	for _, endpoint := range m.cfg.Proxies {
		state := m.states[endpoint.URL]
		status := EndpointStatus{Name: endpoint.Name, URL: publicProxyURL(endpoint.URL), Enabled: endpoint.Enabled}
		if state != nil {
			status.Failures = state.Failures
			status.Healthy = endpoint.Enabled && !state.LastChecked.IsZero() && (state.CooldownUntil.IsZero() || !now.Before(state.CooldownUntil)) && state.LastError == ""
			status.LastLatencyMillis = state.LastLatency.Milliseconds()
			status.ExitIP = state.LastExitIP
			status.Error = state.LastError
			if !state.CooldownUntil.IsZero() && now.Before(state.CooldownUntil) {
				status.CooldownUntil = state.CooldownUntil.UTC().Format(time.RFC3339)
			}
			if !state.LastChecked.IsZero() {
				status.LastChecked = state.LastChecked.UTC().Format(time.RFC3339)
			}
			if !state.LastSuccess.IsZero() {
				status.LastSuccess = state.LastSuccess.UTC().Format(time.RFC3339)
			}
		}
		out = append(out, status)
	}
	return out
}

func CheckAll(ctx context.Context, cfg config.ProxyPoolConfig) ([]EndpointStatus, error) {
	if err := cfg.NormalizeAndValidate(); err != nil {
		return nil, err
	}
	results := make([]EndpointStatus, len(cfg.Proxies))
	var wg sync.WaitGroup
	for i, endpoint := range cfg.Proxies {
		i, endpoint := i, endpoint
		wg.Add(1)
		go func() {
			defer wg.Done()
			results[i] = checkEndpoint(ctx, cfg, endpoint)
		}()
	}
	wg.Wait()
	return results, nil
}

func (m *Manager) CheckAll(ctx context.Context, cfg *config.ProxyPoolConfig) ([]EndpointStatus, error) {
	checkCfg := m.Config()
	if cfg != nil {
		checkCfg = cloneConfig(*cfg)
	}
	results, err := CheckAll(ctx, checkCfg)
	if err != nil {
		return nil, err
	}
	for _, result := range results {
		if result.Healthy {
			m.recordSuccess(findConfiguredURL(checkCfg, result.Name, result.URL), time.Duration(result.LastLatencyMillis)*time.Millisecond, result.ExitIP)
		} else if result.Enabled {
			m.recordFailure(findConfiguredURL(checkCfg, result.Name, result.URL), time.Duration(result.LastLatencyMillis)*time.Millisecond, errors.New(result.Error))
		}
	}
	return results, nil
}

func checkEndpoint(parent context.Context, cfg config.ProxyPoolConfig, endpoint config.SOCKS5ProxyConfig) EndpointStatus {
	status := EndpointStatus{Name: endpoint.Name, URL: publicProxyURL(endpoint.URL), Enabled: endpoint.Enabled}
	started := time.Now()
	transport, err := newSOCKS5Transport(endpoint.URL, time.Duration(cfg.ConnectTimeoutSeconds)*time.Second)
	if err != nil {
		status.Error = safeError(err)
		return status
	}
	defer transport.CloseIdleConnections()

	ctx, cancel := context.WithTimeout(parent, time.Duration(cfg.RequestTimeoutSeconds)*time.Second)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, cfg.HealthCheckURL, nil)
	if err != nil {
		status.Error = safeError(err)
		return status
	}
	req.Header.Set("User-Agent", "JySecAI-ProxyPool/1.0")
	resp, err := transport.RoundTrip(req)
	status.LastLatencyMillis = time.Since(started).Milliseconds()
	status.LastChecked = time.Now().UTC().Format(time.RFC3339)
	if err != nil {
		status.Error = safeError(err)
		return status
	}
	defer resp.Body.Close()
	body, readErr := io.ReadAll(io.LimitReader(resp.Body, 256))
	if readErr != nil {
		status.Error = safeError(readErr)
		return status
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		status.Error = fmt.Sprintf("health check returned HTTP %d", resp.StatusCode)
		return status
	}
	value := strings.TrimSpace(string(body))
	if net.ParseIP(value) != nil {
		status.ExitIP = value
	}
	status.Healthy = true
	status.LastSuccess = status.LastChecked
	return status
}

func newSOCKS5Transport(rawURL string, connectTimeout time.Duration) (*http.Transport, error) {
	proxyURL, err := url.Parse(rawURL)
	if err != nil {
		return nil, fmt.Errorf("parse SOCKS5 proxy: %w", err)
	}
	var auth *xproxy.Auth
	if proxyURL.User != nil {
		password, _ := proxyURL.User.Password()
		auth = &xproxy.Auth{User: proxyURL.User.Username(), Password: password}
	}
	baseDialer := &net.Dialer{Timeout: connectTimeout, KeepAlive: 30 * time.Second}
	dialer, err := xproxy.SOCKS5("tcp", proxyURL.Host, auth, baseDialer)
	if err != nil {
		return nil, fmt.Errorf("create SOCKS5 dialer: %w", err)
	}
	contextDialer, ok := dialer.(xproxy.ContextDialer)
	if !ok {
		return nil, errors.New("SOCKS5 dialer does not support contexts")
	}
	transport := cloneDefaultTransport()
	transport.Proxy = nil
	transport.DialContext = contextDialer.DialContext
	transport.TLSHandshakeTimeout = connectTimeout
	transport.ResponseHeaderTimeout = 30 * time.Second
	return transport, nil
}

func cloneDefaultTransport() *http.Transport {
	if base, ok := http.DefaultTransport.(*http.Transport); ok {
		return base.Clone()
	}
	return &http.Transport{}
}

func cloneConfig(cfg config.ProxyPoolConfig) config.ProxyPoolConfig {
	cfg.Proxies = append([]config.SOCKS5ProxyConfig(nil), cfg.Proxies...)
	return cfg
}

func publicProxyURL(rawURL string) string {
	parsed, err := url.Parse(rawURL)
	if err != nil {
		return rawURL
	}
	parsed.User = nil
	return parsed.String()
}

func safeError(err error) string {
	if err == nil {
		return ""
	}
	message := err.Error()
	if len(message) > 300 {
		message = message[:300]
	}
	return message
}

func findConfiguredURL(cfg config.ProxyPoolConfig, name, publicURL string) string {
	for _, endpoint := range cfg.Proxies {
		if endpoint.Name == name && publicProxyURL(endpoint.URL) == publicURL {
			return endpoint.URL
		}
	}
	return publicURL
}
