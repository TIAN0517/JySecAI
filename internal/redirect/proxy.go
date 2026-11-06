package redirect

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"golang.org/x/net/proxy"
)

// 代理支援。
//
// 批次驗證與巡站都可能需要掛代理：目標站在特定地區、機房出口被風控、或需要固定
// 出口 IP 做前後對照。支援的協定：
//
//	http://    一般 HTTP 代理
//	https://   以 TLS 連線的 HTTP 代理
//	socks5://  SOCKS5（帳密驗證），域名在本機解析
//	socks5h:// SOCKS5，域名交給代理端解析
//	socks4://  SOCKS4（userid 驗證），域名在本機解析
//	socks4a:// SOCKS4a，域名交給代理端解析

const (
	// socks4Version 是 SOCKS4 協定版本號。
	socks4Version = 4
	// socks4Connect 是 SOCKS4 的 CONNECT 命令。
	socks4Connect = 1
	// socks4Granted 是 SOCKS4 回應中代表「允許」的代碼。
	socks4Granted = 90
	// socks4Rejected 是 SOCKS4 回應中代表「拒絕」的代碼。
	socks4Rejected = 91
	// socks4IdentdUnavailable 是代理端無法回應 identd 的代碼。
	socks4IdentdUnavailable = 92
	// socks4UserMismatch 是 userid 不符的代碼。
	socks4UserMismatch = 93
)

// NewProxyClient 依代理網址建立 HTTP client。
//
// proxyURL 為空時回傳 nil（呼叫端自行決定直連）。支援 http、https、socks5、socks5h、
// socks4、socks4a；其他協定直接回錯，不會默默直連。
func NewProxyClient(proxyURL string, timeout time.Duration) (*http.Client, error) {
	raw := strings.TrimSpace(proxyURL)
	if raw == "" {
		return nil, nil
	}
	parsed, err := url.Parse(raw)
	if err != nil {
		return nil, fmt.Errorf("代理網址解析失敗: %w", err)
	}
	if parsed.Host == "" {
		return nil, errors.New("代理網址缺少主機")
	}
	if timeout <= 0 {
		timeout = DefaultProbeTimeout
	}

	transport := &http.Transport{
		TLSHandshakeTimeout:   10 * time.Second,
		ResponseHeaderTimeout: timeout,
		MaxIdleConns:          32,
		IdleConnTimeout:       90 * time.Second,
	}

	switch strings.ToLower(parsed.Scheme) {
	case "http", "https":
		transport.Proxy = http.ProxyURL(parsed)
	case "socks5", "socks5h":
		dialer, err := newSocks5Dialer(parsed, strings.EqualFold(parsed.Scheme, "socks5h"))
		if err != nil {
			return nil, err
		}
		transport.DialContext = dialer.DialContext
	case "socks4", "socks4a":
		transport.DialContext = newSocks4DialContext(parsed, strings.EqualFold(parsed.Scheme, "socks4a"))
	default:
		return nil, fmt.Errorf("不支援的代理協定 %q（可用：http、https、socks5、socks5h、socks4、socks4a）", parsed.Scheme)
	}

	return &http.Client{Timeout: timeout, Transport: transport}, nil
}

// newSocks5Dialer 建立 SOCKS5 dialer。
//
// remoteDNS 為 true 時把域名交給代理端解析（socks5h）；false 時在本機先解析成 IP
// 再送給代理端，避免域名解析曝露在本機。
func newSocks5Dialer(proxyURL *url.URL, remoteDNS bool) (proxy.ContextDialer, error) {
	auth := &proxy.Auth{}
	if proxyURL.User != nil {
		auth.User = proxyURL.User.Username()
		auth.Password, _ = proxyURL.User.Password()
	}
	address := proxyURL.Host
	if _, _, err := net.SplitHostPort(address); err != nil {
		address = net.JoinHostPort(address, "1080")
	}
	base, err := proxy.SOCKS5("tcp", address, auth, proxy.Direct)
	if err != nil {
		return nil, fmt.Errorf("建立 SOCKS5 代理失敗: %w", err)
	}
	dialer, ok := base.(proxy.ContextDialer)
	if !ok {
		return nil, errors.New("SOCKS5 代理不支援 context")
	}
	if remoteDNS {
		return dialer, nil
	}
	return &localResolveSOCKS5Dialer{dialer: dialer}, nil
}

// localResolveSOCKS5Dialer 在本機解析域名後再交給 SOCKS5 代理。
type localResolveSOCKS5Dialer struct {
	dialer proxy.ContextDialer
}

func (d *localResolveSOCKS5Dialer) DialContext(ctx context.Context, network, address string) (net.Conn, error) {
	host, port, err := net.SplitHostPort(address)
	if err != nil {
		return d.dialer.DialContext(ctx, network, address)
	}
	if net.ParseIP(host) != nil {
		return d.dialer.DialContext(ctx, network, address)
	}
	ips, err := net.DefaultResolver.LookupIPAddr(ctx, host)
	if err != nil || len(ips) == 0 {
		if err == nil {
			err = fmt.Errorf("域名 %s 無法解析", host)
		}
		return nil, err
	}
	return d.dialer.DialContext(ctx, network, net.JoinHostPort(ips[0].IP.String(), port))
}

// newSocks4DialContext 建立 SOCKS4 / SOCKS4a 的 dial function。
//
// SOCKS4 只有 userid（沒有密碼）。remoteDNS 為 true 時走 SOCKS4a：把
// DSTIP 標成 0.0.0.1 並在 userid 之後附上域名，由代理端解析。
func newSocks4DialContext(proxyURL *url.URL, remoteDNS bool) func(context.Context, string, string) (net.Conn, error) {
	proxyAddress := proxyURL.Host
	if _, _, err := net.SplitHostPort(proxyAddress); err != nil {
		proxyAddress = net.JoinHostPort(proxyAddress, "1080")
	}
	userID := ""
	if proxyURL.User != nil {
		userID = proxyURL.User.Username()
	}
	return func(ctx context.Context, network, address string) (net.Conn, error) {
		return dialSOCKS4(ctx, network, proxyAddress, userID, address, remoteDNS)
	}
}

// dialSOCKS4 執行一次 SOCKS4 CONNECT。
func dialSOCKS4(ctx context.Context, network, proxyAddress, userID, address string, remoteDNS bool) (net.Conn, error) {
	host, portValue, err := net.SplitHostPort(address)
	if err != nil {
		return nil, fmt.Errorf("目標位址解析失敗: %w", err)
	}
	port, err := strconv.Atoi(portValue)
	if err != nil || port <= 0 || port > 65535 {
		return nil, fmt.Errorf("目標埠號無效: %q", portValue)
	}

	var ipBytes [4]byte
	appendHostname := ""
	if ip := net.ParseIP(host); ip != nil {
		if v4 := ip.To4(); v4 != nil {
			copy(ipBytes[:], v4)
		} else {
			// SOCKS4 只支援 IPv4；IPv6 目標沒有對應的編碼方式。
			return nil, errors.New("SOCKS4 不支援 IPv6 目標")
		}
	} else if remoteDNS {
		// SOCKS4a：0.0.0.x（x 非 0）代表後面附著域名。
		ipBytes = [4]byte{0, 0, 0, 1}
		appendHostname = host
	} else {
		ips, err := net.DefaultResolver.LookupIPAddr(ctx, host)
		if err != nil {
			return nil, err
		}
		for _, candidate := range ips {
			if v4 := candidate.IP.To4(); v4 != nil {
				copy(ipBytes[:], v4)
				break
			}
		}
	}

	dialer := &net.Dialer{Timeout: 15 * time.Second}
	conn, err := dialer.DialContext(ctx, "tcp", proxyAddress)
	if err != nil {
		return nil, fmt.Errorf("連線 SOCKS4 代理失敗: %w", err)
	}

	request := make([]byte, 0, 9+len(userID)+1+len(appendHostname))
	request = append(request, socks4Version, socks4Connect)
	request = append(request, byte(port>>8), byte(port))
	request = append(request, ipBytes[:]...)
	request = append(request, []byte(userID)...)
	request = append(request, 0)
	if appendHostname != "" {
		request = append(request, []byte(appendHostname)...)
		request = append(request, 0)
	}

	if deadline, ok := ctx.Deadline(); ok {
		_ = conn.SetDeadline(deadline)
	}
	if _, err := conn.Write(request); err != nil {
		conn.Close()
		return nil, fmt.Errorf("送出 SOCKS4 請求失敗: %w", err)
	}

	response := make([]byte, 8)
	if _, err := io.ReadFull(conn, response); err != nil {
		conn.Close()
		return nil, fmt.Errorf("讀取 SOCKS4 回應失敗: %w", err)
	}
	_ = conn.SetDeadline(time.Time{})
	switch response[1] {
	case socks4Granted:
		return conn, nil
	case socks4Rejected:
		conn.Close()
		return nil, errors.New("SOCKS4 代理拒絕了請求")
	case socks4IdentdUnavailable:
		conn.Close()
		return nil, errors.New("SOCKS4 代理無法回應 identd")
	case socks4UserMismatch:
		conn.Close()
		return nil, errors.New("SOCKS4 代理的 userid 不符")
	default:
		conn.Close()
		return nil, fmt.Errorf("SOCKS4 代理回應未知代碼 %d", response[1])
	}
}

// MaskProxyURL 把代理網址的帳密換成遮蔽佔位符。
//
// 代理網址常帶供應商帳密，批次紀錄與報告都會存下「當時用了哪個出口」，
// 因此存檔前必須遮蔽 userinfo。
func MaskProxyURL(raw string) string {
	trimmed := strings.TrimSpace(raw)
	if trimmed == "" {
		return ""
	}
	parsed, err := url.Parse(trimmed)
	if err != nil || parsed.User == nil {
		return trimmed
	}
	parsed.User = url.User("********")
	return parsed.String()
}
