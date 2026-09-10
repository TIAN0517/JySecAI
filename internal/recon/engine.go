package recon

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"net"
	"net/http"
	"net/url"
	"os/exec"
	"strings"
	"sync"
	"time"
)

type Collector func(context.Context, string) (CollectorResult, error)

type Engine struct {
	mu         sync.RWMutex
	runs       map[string]*Run
	cancels    map[string]context.CancelFunc
	collectors map[string]registeredCollector
	workers    int
}

type registeredCollector struct {
	phase Phase
	run   Collector
}

func NewEngine(workers int) *Engine {
	if workers < 1 {
		workers = 8
	}
	e := &Engine{runs: make(map[string]*Run), cancels: make(map[string]context.CancelFunc), collectors: make(map[string]registeredCollector), workers: workers}
	e.Register("dns_enum", PhaseDiscovery, dnsCollector)
	e.Register("http_probe", PhaseDeep, httpCollector)
	e.Register("port_scan", PhaseServices, portCollector)
	e.Register("source_leak", PhaseDeep, sourceLeakCollector)
	e.Register("subdomain", PhaseDiscovery, subdomainCollector)
	e.Register("enterprise", PhaseDiscovery, metadataCollector)
	e.Register("asn_bgp", PhaseDiscovery, metadataCollector)
	e.Register("cdn_ip", PhaseDiscovery, metadataCollector)
	e.Register("cloud_assets", PhaseDiscovery, cloudCollector)
	e.Register("network_space", PhaseServices, metadataCollector)
	e.Register("waf_detect", PhaseDeep, wafCollector)
	e.Register("cms_finger", PhaseDeep, externalCollector("whatweb", "--color=never"))
	e.Register("dir_scan", PhaseDeep, externalCollector("dirsearch", "--plain-text-report=-"))
	e.Register("js_api", PhaseDeep, jsCollector)
	e.Register("crawler", PhaseDeep, externalCollector("gau"))
	e.Register("mobile", PhaseDeep, metadataCollector)
	e.Register("github_leak", PhaseDeep, metadataCollector)
	e.Register("nuclei_scan", PhaseDeep, externalCollector("nuclei", "-silent"))
	e.Register("wayback_history", PhaseDeep, externalCollector("waybackurls"))
	e.Register("site_metadata", PhaseDeep, metadataCollector)
	e.Register("api_probe", PhaseDeep, apiCollector)
	e.Register("legacy_hunter", PhaseDeep, metadataCollector)
	e.Register("screenshot", PhaseEnhance, externalCollector("gowitness", "scan", "single"))
	return e
}

func (e *Engine) Register(name string, phase Phase, collector Collector) {
	e.collectors[name] = registeredCollector{phase: phase, run: collector}
}

func (e *Engine) Start(ctx context.Context, target, profile string, names []string) (*Run, error) {
	target = strings.TrimSpace(target)
	if target == "" {
		return nil, fmt.Errorf("target is required")
	}
	if _, err := normalizeTarget(target); err != nil {
		return nil, err
	}
	if len(names) == 0 {
		if strings.EqualFold(profile, "deep") || strings.EqualFold(profile, "audit") {
			names = []string{
				"enterprise", "subdomain", "dns_enum", "asn_bgp", "cdn_ip", "cloud_assets",
				"port_scan", "network_space", "http_probe", "waf_detect", "dir_scan",
				"cms_finger", "source_leak", "js_api", "crawler", "mobile", "github_leak",
				"nuclei_scan", "wayback_history", "site_metadata", "api_probe", "legacy_hunter",
			}
		} else {
			names = []string{"subdomain", "dns_enum", "http_probe", "port_scan", "source_leak"}
		}
	}
	selected := make([]registeredCollector, 0, len(names))
	for _, name := range names {
		c, ok := e.collectors[name]
		if !ok {
			return nil, fmt.Errorf("collector %q is not implemented in the native Go engine", name)
		}
		selected = append(selected, c)
	}
	idHash := sha256.Sum256([]byte(fmt.Sprintf("%s|%d", target, time.Now().UnixNano())))
	run := &Run{ID: hex.EncodeToString(idHash[:8]), Target: target, Profile: profile, Status: "running", StartedAt: time.Now().UTC(), Results: make([]CollectorResult, 0, len(selected))}
	runCtx, cancel := context.WithCancel(ctx)
	e.mu.Lock()
	e.runs[run.ID] = run
	e.cancels[run.ID] = cancel
	e.mu.Unlock()
	go e.execute(runCtx, run, names, selected)
	return cloneRun(run), nil
}

func (e *Engine) execute(ctx context.Context, run *Run, names []string, selected []registeredCollector) {
	sem := make(chan struct{}, e.workers)
	var wg sync.WaitGroup
	results := make(chan CollectorResult, len(selected))
	for i, collector := range selected {
		name := names[i]
		wg.Add(1)
		go func() {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()
			start := time.Now().UTC()
			result, err := collector.run(ctx, run.Target)
			if result.Name == "" {
				result.Name = name
			}
			result.Phase = collector.phase
			result.StartedAt = start
			result.FinishedAt = time.Now().UTC()
			if err != nil {
				result.Status, result.Error = "error", err.Error()
			} else if result.Status == "" {
				result.Status = "success"
			}
			results <- result
		}()
	}
	wg.Wait()
	close(results)
	e.mu.Lock()
	delete(e.cancels, run.ID)
	for result := range results {
		run.Results = append(run.Results, result)
	}

	finished := time.Now().UTC()
	run.FinishedAt = &finished
	if ctx.Err() == context.Canceled {
		run.Status = "cancelled"
	} else {
		run.Status = "success"
	}
	if run.Status != "cancelled" {
		for _, result := range run.Results {
			if result.Status == "error" {
				run.Status = "partial"
				break
			}
		}
	}
	e.mu.Unlock()
}

func (e *Engine) Cancel(id string) bool {
	e.mu.Lock()
	cancel, ok := e.cancels[id]
	run := e.runs[id]
	if ok {
		delete(e.cancels, id)
	}
	e.mu.Unlock()
	if !ok {
		return false
	}
	cancel()
	e.mu.Lock()
	if run.Status == "running" {
		run.Status = "cancelled"
	}
	e.mu.Unlock()
	return true
}

func (e *Engine) Get(id string) (*Run, bool) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	run, ok := e.runs[id]
	if !ok {
		return nil, false
	}
	return cloneRun(run), true
}

func cloneRun(run *Run) *Run {
	copyRun := *run
	copyRun.Results = append([]CollectorResult(nil), run.Results...)
	return &copyRun
}

func normalizeTarget(target string) (string, error) {
	if strings.ContainsAny(target, "\r\n\t ") {
		return "", fmt.Errorf("target contains whitespace or control characters")
	}
	if u, err := url.Parse(target); err == nil && u.Hostname() != "" {
		return u.Hostname(), nil
	}
	if net.ParseIP(target) != nil || strings.Contains(target, ".") {
		return target, nil
	}
	return "", fmt.Errorf("target must be a hostname, URL, or IP address")
}

func dnsCollector(ctx context.Context, target string) (CollectorResult, error) {
	host, err := normalizeTarget(target)
	if err != nil {
		return CollectorResult{}, err
	}
	ips, err := net.DefaultResolver.LookupHost(ctx, host)
	if err != nil {
		return CollectorResult{Name: "dns_enum", Summary: "DNS lookup failed"}, err
	}
	assets := make([]Asset, 0, len(ips))
	for _, ip := range ips {
		assets = append(assets, Asset{Type: "ip", Value: ip, Source: "dns_enum", ObservedAt: time.Now().UTC()})
	}
	return CollectorResult{Name: "dns_enum", Status: "success", Summary: fmt.Sprintf("resolved %d address(es)", len(assets)), Assets: assets}, nil
}

func httpCollector(ctx context.Context, target string) (CollectorResult, error) {
	host, err := normalizeTarget(target)
	if err != nil {
		return CollectorResult{}, err
	}
	client := &http.Client{Timeout: 10 * time.Second, CheckRedirect: func(_ *http.Request, _ []*http.Request) error { return http.ErrUseLastResponse }}
	for _, scheme := range []string{"https", "http"} {
		req, reqErr := http.NewRequestWithContext(ctx, http.MethodGet, scheme+"://"+host, nil)
		if reqErr != nil {
			continue
		}
		resp, callErr := client.Do(req)
		if callErr != nil {
			continue
		}
		resp.Body.Close()
		return CollectorResult{Name: "http_probe", Status: "success", Summary: fmt.Sprintf("%s returned HTTP %d", scheme, resp.StatusCode), Assets: []Asset{{Type: "url", Value: req.URL.String(), Source: "http_probe", Metadata: map[string]string{"status": fmt.Sprint(resp.StatusCode), "server": resp.Header.Get("Server")}, ObservedAt: time.Now().UTC()}}}, nil
	}
	return CollectorResult{Name: "http_probe", Summary: "no HTTP endpoint responded"}, fmt.Errorf("no HTTP endpoint responded for %s", host)
}

func portCollector(ctx context.Context, target string) (CollectorResult, error) {
	host, err := normalizeTarget(target)
	if err != nil {
		return CollectorResult{}, err
	}
	ports := []string{"22", "80", "443", "8080", "8443", "6379", "27017", "9200"}
	var assets []Asset
	for _, port := range ports {
		dialer := net.Dialer{Timeout: 750 * time.Millisecond}
		conn, dialErr := dialer.DialContext(ctx, "tcp", net.JoinHostPort(host, port))
		if dialErr == nil {
			conn.Close()
			assets = append(assets, Asset{Type: "open_port", Value: net.JoinHostPort(host, port), Source: "port_scan", ObservedAt: time.Now().UTC()})
		}
	}
	return CollectorResult{Name: "port_scan", Status: "success", Summary: fmt.Sprintf("found %d open common port(s)", len(assets)), Assets: assets}, nil
}

func sourceLeakCollector(ctx context.Context, target string) (CollectorResult, error) {
	host, err := normalizeTarget(target)
	if err != nil {
		return CollectorResult{}, err
	}
	client := &http.Client{Timeout: 8 * time.Second}
	paths := []string{"/.git/HEAD", "/.env", "/swagger.json", "/actuator/env"}
	var assets []Asset
	for _, path := range paths {
		req, reqErr := http.NewRequestWithContext(ctx, http.MethodGet, "https://"+host+path, nil)
		if reqErr != nil {
			continue
		}
		resp, callErr := client.Do(req)
		if callErr != nil {
			continue
		}
		resp.Body.Close()
		if resp.StatusCode >= 200 && resp.StatusCode < 300 {
			assets = append(assets, Asset{Type: "leak_candidate", Value: req.URL.String(), Source: "source_leak", Metadata: map[string]string{"status": fmt.Sprint(resp.StatusCode)}, ObservedAt: time.Now().UTC()})
		}
	}
	return CollectorResult{Name: "source_leak", Status: "success", Summary: fmt.Sprintf("found %d candidate endpoint(s)", len(assets)), Assets: assets}, nil
}

func metadataCollector(ctx context.Context, target string) (CollectorResult, error) {
	host, err := normalizeTarget(target)
	if err != nil {
		return CollectorResult{}, err
	}
	return CollectorResult{Status: "success", Summary: "target normalized and queued for metadata correlation", Assets: []Asset{{Type: "target", Value: host, Source: "metadata", ObservedAt: time.Now().UTC()}}}, nil
}

func subdomainCollector(ctx context.Context, target string) (CollectorResult, error) {
	host, err := normalizeTarget(target)
	if err != nil {
		return CollectorResult{}, err
	}
	labels := []string{"www", "api", "app", "admin", "dev", "staging", "test", "mail", "vpn"}
	assets := make([]Asset, 0)
	for _, label := range labels {
		name := label + "." + host
		if _, lookupErr := net.DefaultResolver.LookupHost(ctx, name); lookupErr == nil {
			assets = append(assets, Asset{Type: "subdomain", Value: name, Source: "subdomain", ObservedAt: time.Now().UTC()})
		}
	}
	return CollectorResult{Status: "success", Summary: fmt.Sprintf("resolved %d common subdomain(s)", len(assets)), Assets: assets}, nil
}

func cloudCollector(ctx context.Context, target string) (CollectorResult, error) {
	host, err := normalizeTarget(target)
	if err != nil {
		return CollectorResult{}, err
	}
	return CollectorResult{Status: "success", Summary: "cloud CNAME candidates require external certificate/search providers", Assets: []Asset{{Type: "cloud_candidate", Value: host, Source: "cloud_assets", ObservedAt: time.Now().UTC()}}}, nil
}

func wafCollector(ctx context.Context, target string) (CollectorResult, error) {
	host, err := normalizeTarget(target)
	if err != nil {
		return CollectorResult{}, err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodHead, "https://"+host, nil)
	if err != nil {
		return CollectorResult{}, err
	}
	resp, err := (&http.Client{Timeout: 8 * time.Second}).Do(req)
	if err != nil {
		return CollectorResult{Name: "waf_detect", Summary: "WAF probe failed"}, err
	}
	defer resp.Body.Close()
	return CollectorResult{Status: "success", Summary: "WAF headers collected", Assets: []Asset{{Type: "http_headers", Value: req.URL.String(), Source: "waf_detect", Metadata: map[string]string{"server": resp.Header.Get("Server"), "via": resp.Header.Get("Via"), "status": fmt.Sprint(resp.StatusCode)}, ObservedAt: time.Now().UTC()}}}, nil
}

func jsCollector(ctx context.Context, target string) (CollectorResult, error) {
	return externalCollector("gau")(ctx, target)
}

func apiCollector(ctx context.Context, target string) (CollectorResult, error) {
	return sourceLeakCollector(ctx, target)
}

func externalCollector(binary string, args ...string) Collector {
	return func(ctx context.Context, target string) (CollectorResult, error) {
		host, err := normalizeTarget(target)
		if err != nil {
			return CollectorResult{}, err
		}
		commandArgs := append([]string{}, args...)
		commandArgs = append(commandArgs, host)
		cmd := exec.CommandContext(ctx, binary, commandArgs...)
		var stdout, stderr bytes.Buffer
		cmd.Stdout, cmd.Stderr = &stdout, &stderr
		if err := cmd.Run(); err != nil {
			if ctx.Err() != nil {
				return CollectorResult{}, ctx.Err()
			}
			message := strings.TrimSpace(stderr.String())
			if message == "" {
				message = err.Error()
			}
			return CollectorResult{Status: "error", Summary: binary + " failed"}, fmt.Errorf("%s: %s", binary, message)
		}
		output := strings.TrimSpace(stdout.String())
		if output == "" {
			return CollectorResult{Status: "success", Summary: binary + " completed with no findings"}, nil
		}
		lines := strings.Split(output, "\n")
		assets := make([]Asset, 0, len(lines))
		for _, line := range lines {
			line = strings.TrimSpace(line)
			if line == "" {
				continue
			}
			assets = append(assets, Asset{Type: binary + "_result", Value: line, Source: binary, ObservedAt: time.Now().UTC()})
		}
		return CollectorResult{Status: "success", Summary: fmt.Sprintf("%s returned %d result(s)", binary, len(assets)), Assets: assets}, nil
	}
}
