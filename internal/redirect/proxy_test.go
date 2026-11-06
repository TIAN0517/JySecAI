package redirect

import (
	"context"
	"encoding/binary"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"testing"
	"time"
)

// 代理層測試。
//
// SOCKS4 是本專案自己實作的（x/net/proxy 只支援 SOCKS5），手寫的協定沒有
// 現成實作可參考，因此這裡用假的 SOCKS 伺服器做端到端驗證：真的走一次握手、
// 真的把流量接到目標，再確認 client 拿得到目標的回應。

func TestNewProxyClientRejectsUnsupportedScheme(t *testing.T) {
	if _, err := NewProxyClient("ftp://127.0.0.1:1080", time.Second); err == nil {
		t.Fatal("expected error for unsupported proxy scheme")
	}
	if _, err := NewProxyClient("http://", time.Second); err == nil {
		t.Fatal("expected error for proxy URL without host")
	}
}

func TestNewProxyClientWithoutProxyReturnsNil(t *testing.T) {
	client, err := NewProxyClient("   ", time.Second)
	if err != nil {
		t.Fatal(err)
	}
	if client != nil {
		t.Fatal("expected nil client when no proxy is configured")
	}
}

func TestNewProxyClientAcceptsSupportedSchemes(t *testing.T) {
	for _, raw := range []string{
		"http://127.0.0.1:8080",
		"https://127.0.0.1:8443",
		"socks5://127.0.0.1:1080",
		"socks5h://127.0.0.1:1080",
		"socks4://127.0.0.1:1080",
		"socks4a://127.0.0.1:1080",
	} {
		client, err := NewProxyClient(raw, 2*time.Second)
		if err != nil {
			t.Fatalf("%s: unexpected error: %v", raw, err)
		}
		if client == nil {
			t.Fatalf("%s: expected a client", raw)
		}
	}
}

func TestMaskProxyURLHidesCredentials(t *testing.T) {
	masked := MaskProxyURL("socks5://user:secret@127.0.0.1:1080")
	if strings.Contains(masked, "secret") || strings.Contains(masked, "user") {
		t.Fatalf("credentials leaked: %q", masked)
	}
	if !strings.Contains(masked, "127.0.0.1:1080") {
		t.Fatalf("host should be preserved: %q", masked)
	}
	if MaskProxyURL("  ") != "" {
		t.Fatal("blank proxy should stay blank")
	}
	if MaskProxyURL("http://127.0.0.1:8080") != "http://127.0.0.1:8080" {
		t.Fatal("proxy without credentials should stay unchanged")
	}
}

func TestSocks5ProxyReachesTarget(t *testing.T) {
	target := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("through-socks5"))
	}))
	defer target.Close()

	proxyServer := startFakeSOCKS5(t)
	defer proxyServer.Close()

	client, err := NewProxyClient("socks5://127.0.0.1:"+proxyPort(t, proxyServer), 5*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	resp, err := client.Get(target.URL)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if !strings.Contains(string(body), "through-socks5") {
		t.Fatalf("unexpected body: %q", body)
	}
}

func TestSocks4ProxyReachesTarget(t *testing.T) {
	target := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("through-socks4"))
	}))
	defer target.Close()

	proxyServer := startFakeSOCKS4(t, nil)
	defer proxyServer.Close()

	client, err := NewProxyClient("socks4://127.0.0.1:"+proxyPort(t, proxyServer), 5*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	resp, err := client.Get(target.URL)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if !strings.Contains(string(body), "through-socks4") {
		t.Fatalf("unexpected body: %q", body)
	}
}

func TestSocks4aProxyResolvesHostnameAtProxy(t *testing.T) {
	target := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("through-socks4a"))
	}))
	defer target.Close()

	// socks4a 把域名交給代理端解析：假的代理把主名對映到 127.0.0.1，
	// 若 client 在本地先解析就會直接失敗，送達即代表主名有交到代理端。
	proxyServer := startFakeSOCKS4(t, func(host string) string { return "127.0.0.1" })
	defer proxyServer.Close()

	// socks4a 把域名交給代理端解析；本地刻意用不可解析的主名，確認請求仍能送達。
	targetHost := target.Listener.Addr().(*net.TCPAddr)
	client, err := NewProxyClient("socks4a://127.0.0.1:"+proxyPort(t, proxyServer), 5*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	requestURL := "http://unresolvable.invalid:" + strconv.Itoa(targetHost.Port) + "/"
	resp, err := client.Get(requestURL)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if !strings.Contains(string(body), "through-socks4a") {
		t.Fatalf("unexpected body: %q", body)
	}
}

func TestSocks4RejectsRefusedConnection(t *testing.T) {
	// 代理回「拒絕」代碼時，client 必須回錯而不是靜默直連。
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	go func() {
		conn, err := listener.Accept()
		if err != nil {
			return
		}
		defer conn.Close()
		buf := make([]byte, 512)
		if _, err := conn.Read(buf); err != nil {
			return
		}
		_, _ = conn.Write([]byte{0x00, socks4Rejected, 0x00, 0x00, 0, 0, 0, 0})
	}()

	client, err := NewProxyClient("socks4://127.0.0.1:"+proxyPort(t, listener), 3*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := client.Get("http://example.invalid/"); err == nil {
		t.Fatal("expected error when the proxy refuses the connection")
	}
}

// proxyPort 取出監聽埠。
func proxyPort(t *testing.T, listener net.Listener) string {
	t.Helper()
	addr, ok := listener.Addr().(*net.TCPAddr)
	if !ok {
		t.Fatalf("unexpected listener address type %T", listener.Addr())
	}
	return strconv.Itoa(addr.Port)
}

// startFakeSOCKS5 啟動一個只做 CONNECT 的最小 SOCKS5 伺服器。
func startFakeSOCKS5(t *testing.T) net.Listener {
	t.Helper()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	go func() {
		for {
			conn, err := listener.Accept()
			if err != nil {
				return
			}
			go handleFakeSOCKS5(conn)
		}
	}()
	return listener
}

func handleFakeSOCKS5(conn net.Conn) {
	defer conn.Close()
	// 認證方法協商：支援「不需驗證」。
	header := make([]byte, 2)
	if _, err := io.ReadFull(conn, header); err != nil {
		return
	}
	methods := make([]byte, header[1])
	if _, err := io.ReadFull(conn, methods); err != nil {
		return
	}
	if _, err := conn.Write([]byte{0x05, 0x00}); err != nil {
		return
	}

	request := make([]byte, 4)
	if _, err := io.ReadFull(conn, request); err != nil {
		return
	}
	var host string
	switch request[3] {
	case 0x01: // IPv4
		addr := make([]byte, 4)
		if _, err := io.ReadFull(conn, addr); err != nil {
			return
		}
		host = net.IP(addr).String()
	case 0x03: // 域名
		length := make([]byte, 1)
		if _, err := io.ReadFull(conn, length); err != nil {
			return
		}
		name := make([]byte, length[0])
		if _, err := io.ReadFull(conn, name); err != nil {
			return
		}
		host = string(name)
	case 0x04: // IPv6
		addr := make([]byte, 16)
		if _, err := io.ReadFull(conn, addr); err != nil {
			return
		}
		host = net.IP(addr).String()
	default:
		return
	}
	portBytes := make([]byte, 2)
	if _, err := io.ReadFull(conn, portBytes); err != nil {
		return
	}
	port := binary.BigEndian.Uint16(portBytes)

	upstream, err := net.DialTimeout("tcp", net.JoinHostPort(host, strconv.Itoa(int(port))), 5*time.Second)
	if err != nil {
		_, _ = conn.Write([]byte{0x05, 0x01, 0x00, 0x01, 0, 0, 0, 0, 0, 0})
		return
	}
	defer upstream.Close()
	if _, err := conn.Write([]byte{0x05, 0x00, 0x00, 0x01, 0, 0, 0, 0, 0, 0}); err != nil {
		return
	}
	pipe(conn, upstream)
}

// startFakeSOCKS4 啟動一個只做 CONNECT 的最小 SOCKS4 伺服器（含 SOCKS4a）。
func startFakeSOCKS4(t *testing.T, resolve func(host string) string) net.Listener {
	t.Helper()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	go func() {
		for {
			conn, err := listener.Accept()
			if err != nil {
				return
			}
			go handleFakeSOCKS4(conn, resolve)
		}
	}()
	return listener
}

func handleFakeSOCKS4(conn net.Conn, resolve func(host string) string) {
	defer conn.Close()
	request := make([]byte, 8)
	if _, err := io.ReadFull(conn, request); err != nil {
		return
	}
	port := binary.BigEndian.Uint16(request[2:4])
	ip := net.IP(request[4:8])

	// userid：直到 NUL 為止。
	userid := make([]byte, 1)
	for {
		if _, err := io.ReadFull(conn, userid); err != nil {
			return
		}
		if userid[0] == 0 {
			break
		}
	}

	host := ip.String()
	if ip[0] == 0 && ip[1] == 0 && ip[2] == 0 && ip[3] != 0 {
		// SOCKS4a：主機名接在 userid 之後。
		name := make([]byte, 1)
		var buffer []byte
		for {
			if _, err := io.ReadFull(conn, name); err != nil {
				return
			}
			if name[0] == 0 {
				break
			}
			buffer = append(buffer, name[0])
		}
		host = string(buffer)
	}
	if resolve != nil {
		host = resolve(host)
	}

	upstream, err := net.DialTimeout("tcp", net.JoinHostPort(host, strconv.Itoa(int(port))), 5*time.Second)
	if err != nil {
		_, _ = conn.Write([]byte{0x00, socks4Rejected, 0x00, 0x00, 0, 0, 0, 0})
		return
	}
	defer upstream.Close()
	if _, err := conn.Write([]byte{0x00, socks4Granted, 0x00, 0x00, 0, 0, 0, 0}); err != nil {
		return
	}
	pipe(conn, upstream)
}

// pipe 雙向轉發兩個連線。
func pipe(left net.Conn, right net.Conn) {
	done := make(chan struct{}, 2)
	go func() {
		_, _ = io.Copy(left, right)
		done <- struct{}{}
	}()
	go func() {
		_, _ = io.Copy(right, left)
		done <- struct{}{}
	}()
	<-done
	_ = left.Close()
	_ = right.Close()
}

// 確認 context 逾時不會讓 dialer 卡住。
func TestProxyDialHonoursContext(t *testing.T) {
	client, err := NewProxyClient("socks5://127.0.0.1:1", 2*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()
	request, err := http.NewRequestWithContext(ctx, http.MethodGet, "http://example.invalid/", nil)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := client.Do(request); err == nil {
		t.Fatal("expected error when the proxy is unreachable")
	}
}
