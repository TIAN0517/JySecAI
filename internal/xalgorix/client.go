package xalgorix

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"strings"
	"time"
)

const maxJSONBytes = 8 << 20
const maxReportBytes = 20 << 20

// Client 只會連到建立時指定的那台 Xalgorix。路徑由呼叫端固定，不能換成別的主機。
type Client struct {
	base  *url.URL
	token string
	http  *http.Client
}

func NewClient(baseURL, token string) (*Client, error) {
	raw := strings.TrimSpace(baseURL)
	parsed, err := url.Parse(raw)
	if err != nil {
		return nil, fmt.Errorf("xalgorix base_url 无效: %w", err)
	}
	if parsed.Scheme != "http" && parsed.Scheme != "https" {
		return nil, errors.New("xalgorix base_url 只接受 http 或 https")
	}
	if parsed.User != nil {
		return nil, errors.New("xalgorix base_url 不能包含账号")
	}
	host := parsed.Hostname()
	if host == "" || parsed.Host == "" {
		return nil, errors.New("xalgorix base_url 缺少主机")
	}
	if ip := net.ParseIP(host); ip != nil && blockedXalgorixIP(ip) {
		return nil, errors.New("xalgorix base_url 指向不允许的地址")
	}
	parsed.Path = strings.TrimRight(parsed.Path, "/")
	parsed.RawQuery = ""
	parsed.Fragment = ""
	allowedHost := parsed.Hostname()
	transport := &http.Transport{
		Proxy: nil,
		DialContext: func(ctx context.Context, network, addr string) (net.Conn, error) {
			dialHost, _, splitErr := net.SplitHostPort(addr)
			if splitErr != nil {
				return nil, splitErr
			}
			if !strings.EqualFold(dialHost, allowedHost) {
				return nil, errors.New("拒绝连接未配置的主机")
			}
			ips, lookupErr := net.DefaultResolver.LookupIPAddr(ctx, dialHost)
			if lookupErr != nil {
				return nil, lookupErr
			}
			if len(ips) == 0 {
				return nil, errors.New("xalgorix 主机没有地址")
			}
			for _, ip := range ips {
				if blockedXalgorixIP(ip.IP) {
					return nil, errors.New("xalgorix 解析到不允许的地址")
				}
			}
			return (&net.Dialer{Timeout: 5 * time.Second, KeepAlive: 30 * time.Second}).DialContext(ctx, network, addr)
		},
	}
	return &Client{
		base:  parsed,
		token: strings.TrimSpace(token),
		http: &http.Client{
			Timeout:   20 * time.Second,
			Transport: transport,
			CheckRedirect: func(req *http.Request, via []*http.Request) error {
				return http.ErrUseLastResponse
			},
		},
	}, nil
}

func (c *Client) Host() string {
	if c == nil || c.base == nil {
		return ""
	}
	return c.base.Hostname()
}

func (c *Client) Status(ctx context.Context) (map[string]any, error) {
	return c.getJSON(ctx, "/api/status")
}

func (c *Client) StartScan(ctx context.Context, body map[string]any) (map[string]any, error) {
	return c.postJSON(ctx, "/api/scan", body)
}

func (c *Client) StopInstance(ctx context.Context, instanceID string) error {
	_, err := c.postJSON(ctx, "/api/instances/"+url.PathEscape(instanceID)+"/stop", map[string]any{})
	return err
}

func (c *Client) Instance(ctx context.Context, instanceID string) (map[string]any, error) {
	return c.getJSON(ctx, "/api/instances/"+url.PathEscape(instanceID))
}

func (c *Client) Events(ctx context.Context, instanceID string) (any, error) {
	return c.getAny(ctx, "/api/instances/"+url.PathEscape(instanceID)+"/events")
}

func (c *Client) Findings(ctx context.Context) (any, error) {
	return c.getAny(ctx, "/api/findings")
}

func (c *Client) Report(ctx context.Context, scanID string) ([]byte, string, error) {
	resp, err := c.do(ctx, http.MethodGet, "/api/report/"+url.PathEscape(scanID), nil)
	if err != nil {
		return nil, "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, "", fmt.Errorf("xalgorix report http %d", resp.StatusCode)
	}
	body, err := io.ReadAll(io.LimitReader(resp.Body, maxReportBytes+1))
	if err != nil {
		return nil, "", err
	}
	if len(body) > maxReportBytes {
		return nil, "", errors.New("xalgorix report 超过大小限制")
	}
	contentType := resp.Header.Get("Content-Type")
	if contentType == "" {
		contentType = "application/pdf"
	}
	return body, contentType, nil
}

func (c *Client) getJSON(ctx context.Context, path string) (map[string]any, error) {
	payload, err := c.getAny(ctx, path)
	if err != nil {
		return nil, err
	}
	object, ok := payload.(map[string]any)
	if !ok {
		return nil, errors.New("xalgorix 响应不是对象")
	}
	return object, nil
}

func (c *Client) getAny(ctx context.Context, path string) (any, error) {
	resp, err := c.do(ctx, http.MethodGet, path, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	return decodeResponse(resp)
}

func (c *Client) postJSON(ctx context.Context, path string, body map[string]any) (map[string]any, error) {
	encoded, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}
	resp, err := c.do(ctx, http.MethodPost, path, encoded)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	payload, err := decodeResponse(resp)
	if err != nil {
		return nil, err
	}
	object, ok := payload.(map[string]any)
	if !ok {
		return map[string]any{"result": payload}, nil
	}
	return object, nil
}

func (c *Client) do(ctx context.Context, method, path string, body []byte) (*http.Response, error) {
	if c == nil || c.base == nil {
		return nil, errors.New("xalgorix 客户端未配置")
	}
	if !strings.HasPrefix(path, "/api/") || strings.Contains(path, "..") || strings.Contains(path, "://") {
		return nil, errors.New("拒绝的 xalgorix 路径")
	}
	endpoint := c.base.JoinPath(path)
	if !strings.EqualFold(endpoint.Hostname(), c.base.Hostname()) {
		return nil, errors.New("拒绝改写 xalgorix 主机")
	}
	var reader io.Reader
	if body != nil {
		reader = bytes.NewReader(body)
	}
	req, err := http.NewRequestWithContext(ctx, method, endpoint.String(), reader)
	if err != nil {
		return nil, err
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	if c.token != "" {
		req.Header.Set("Authorization", "Bearer "+c.token)
	}
	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode >= 300 && resp.StatusCode < 400 {
		resp.Body.Close()
		return nil, errors.New("xalgorix 返回了重定向，已拒绝跟随")
	}
	return resp, nil
}

func decodeResponse(resp *http.Response) (any, error) {
	raw, err := io.ReadAll(io.LimitReader(resp.Body, maxJSONBytes+1))
	if err != nil {
		return nil, err
	}
	if len(raw) > maxJSONBytes {
		return nil, errors.New("xalgorix 响应超过大小限制")
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("xalgorix http %d", resp.StatusCode)
	}
	if len(bytes.TrimSpace(raw)) == 0 {
		return map[string]any{}, nil
	}
	var payload any
	if err := json.Unmarshal(raw, &payload); err != nil {
		return nil, fmt.Errorf("xalgorix 响应不是 JSON: %w", err)
	}
	return payload, nil
}

func blockedXalgorixIP(ip net.IP) bool {
	if ip == nil || ip.IsUnspecified() || ip.IsLinkLocalUnicast() || ip.IsLinkLocalMulticast() || ip.IsInterfaceLocalMulticast() {
		return true
	}
	if v4 := ip.To4(); v4 != nil && v4[0] == 169 && v4[1] == 254 {
		return true
	}
	return false
}
