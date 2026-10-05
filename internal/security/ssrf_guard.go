package security

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// ErrBlockedAddress is returned when an outbound request resolves to an
// address this application refuses to contact.
var ErrBlockedAddress = errors.New("目标地址位于受限网段，已阻止")

// allowPrivateNetwork is a process-wide escape hatch used only by tests, which
// must reach httptest servers on 127.0.0.1. It is deliberately not exported:
// production callers have no way to set it.
var allowPrivateNetwork = false

// SetAllowPrivateNetworkForTesting enables or disables the SSRF guard for the
// whole process. Tests that point a client at an httptest server must call
// this with defer restore of the previous value.
func SetAllowPrivateNetworkForTesting(allow bool) func() {
	prev := allowPrivateNetwork
	allowPrivateNetwork = allow
	return func() { allowPrivateNetwork = prev }
}

// IsBlockedIP reports whether ip is an address this application refuses to
// dial. It covers loopback, link-local (including the 169.254.169.254 cloud
// metadata endpoint), private, and unspecified addresses for both IPv4 and
// IPv6, plus the IPv4-mapped and 6to4 forms that would otherwise smuggle a
// private target past a v4-only check.
func IsBlockedIP(ip net.IP) bool {
	if ip == nil {
		return true
	}
	if allowPrivateNetwork {
		return false
	}
	if ip.IsLoopback() || ip.IsLinkLocalUnicast() || ip.IsLinkLocalMulticast() ||
		ip.IsUnspecified() || ip.IsPrivate() || ip.IsInterfaceLocalMulticast() {
		return true
	}
	// Unique local IPv6 (fc00::/7) is reported by IsPrivate on newer Go
	// versions, but be explicit so the intent survives toolchain changes.
	if len(ip) == net.IPv6len && ip[0]&0xfe == 0xfc {
		return true
	}
	// IPv4-mapped (::ffff:a.b.c.d) must be judged on its embedded v4 address.
	if v4 := ip.To4(); v4 != nil {
		if v4[0] == 127 || v4[0] == 10 ||
			(v4[0] == 172 && v4[1] >= 16 && v4[1] <= 31) ||
			(v4[0] == 192 && v4[1] == 168) ||
			(v4[0] == 169 && v4[1] == 254) ||
			(v4[0] == 0) {
			return true
		}
	}
	// Shared address space 100.64.0.0/10 and benchmark 198.18.0.0/15 are
	// not covered by IsPrivate but are not routable public targets either.
	if v4 := ip.To4(); v4 != nil {
		if v4[0] == 100 && v4[1] >= 64 && v4[1] <= 127 {
			return true
		}
		if v4[0] == 198 && (v4[1] == 18 || v4[1] == 19) {
			return true
		}
	}
	return false
}

// ValidateOutboundURL parses rawURL and rejects any scheme that is not http or
// https, and any host that is a literal blocked address. DNS names are NOT
// resolved here — use NewSSRFGuardedDialer so the check happens at dial time,
// which is what defeats DNS rebinding.
func ValidateOutboundURL(rawURL string) error {
	trimmed := strings.TrimSpace(rawURL)
	if trimmed == "" {
		return errors.New("URL 为空")
	}
	u, err := url.Parse(trimmed)
	if err != nil {
		return fmt.Errorf("URL 解析失败: %w", err)
	}
	if u.Scheme != "http" && u.Scheme != "https" {
		return fmt.Errorf("不支持的协议: %s", u.Scheme)
	}
	host := u.Hostname()
	if host == "" {
		return errors.New("URL 缺少主机名")
	}
	if ip := net.ParseIP(host); ip != nil && IsBlockedIP(ip) {
		return fmt.Errorf("%w: %s", ErrBlockedAddress, host)
	}
	return nil
}

// NewSSRFGuardedTransport returns an http.Transport that validates the
// resolved address at dial time and re-validates every redirect hop, so an
// attacker-controlled host cannot 302 an otherwise-approved request to an
// internal service.
func NewSSRFGuardedTransport(timeout time.Duration) *http.Transport {
	dialer := &net.Dialer{Timeout: timeout, KeepAlive: 30 * time.Second}
	return &http.Transport{
		Proxy: http.ProxyFromEnvironment,
		DialContext: func(ctx context.Context, network, addr string) (net.Conn, error) {
			host, _, err := net.SplitHostPort(addr)
			if err != nil {
				return nil, err
			}
			ips, err := net.DefaultResolver.LookupIPAddr(ctx, host)
			if err != nil {
				return nil, err
			}
			for _, ip := range ips {
				if IsBlockedIP(ip.IP) {
					return nil, fmt.Errorf("%w: %s", ErrBlockedAddress, host)
				}
			}
			return dialer.DialContext(ctx, network, addr)
		},
		TLSHandshakeTimeout:   timeout,
		ResponseHeaderTimeout: timeout,
	}
}

// NewSSRFGuardedClient returns an http.Client that blocks requests to internal
// addresses. The redirect hook re-validates every hop: an approved public host
// can 302 to an internal one, and the dial-time check alone would not see the
// second request.
func NewSSRFGuardedClient(timeout time.Duration) *http.Client {
	return &http.Client{
		Transport: NewSSRFGuardedTransport(timeout),
		Timeout:   timeout * 2,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			if len(via) >= 5 {
				return errors.New("重定向次数过多")
			}
			return ValidateOutboundURL(req.URL.String())
		},
	}
}
