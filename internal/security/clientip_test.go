package security

import (
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

// newIPContext 造一個帶指定對端位址與 CF-Connecting-IP 的請求 context。
func newIPContext(remoteAddr, cfIP string) *gin.Context {
	gin.SetMode(gin.TestMode)
	c, _ := gin.CreateTestContext(httptest.NewRecorder())
	req := httptest.NewRequest("GET", "/", nil)
	req.RemoteAddr = remoteAddr
	if cfIP != "" {
		req.Header.Set("CF-Connecting-IP", cfIP)
	}
	c.Request = req
	return c
}

// TestEffectiveClientIP 釘死限流鍵的解析規則。
//
// 這台機器上 tunnel／portproxy 進來的請求對端全是 127.0.0.1，若限流直接用
// 對端 IP，全站共用一個桶 → 外部打滿 10 次/分就能鎖死整站登入。
func TestEffectiveClientIP(t *testing.T) {
	cases := []struct {
		name       string
		remoteAddr string
		cfIP       string
		trust      bool
		want       string
	}{
		{"trust off 採對端", "127.0.0.1:1234", "203.0.113.7", false, "127.0.0.1"},
		{"trust on + loopback 採 CF 標頭", "127.0.0.1:1234", "203.0.113.7", true, "203.0.113.7"},
		{"trust on + 非 loopback 仍採對端", "198.51.100.9:5555", "203.0.113.7", true, "198.51.100.9"},
		{"trust on + 缺標頭採對端", "127.0.0.1:1234", "", true, "127.0.0.1"},
		{"trust on + 標頭非法採對端", "127.0.0.1:1234", "not-an-ip", true, "127.0.0.1"},
		{"trust on + IPv6 loopback 採 CF 標頭", "[::1]:1234", "203.0.113.7", true, "203.0.113.7"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := EffectiveClientIP(newIPContext(tc.remoteAddr, tc.cfIP), tc.trust)
			if got != tc.want {
				t.Fatalf("EffectiveClientIP = %q, want %q", got, tc.want)
			}
		})
	}
}

// TestEffectiveClientIPNilContext 不接受 nil（稽核服務在沒有 context 時會呼叫）。
func TestEffectiveClientIPNilContext(t *testing.T) {
	if got := EffectiveClientIP(nil, true); got != "" {
		t.Fatalf("EffectiveClientIP(nil) = %q, want empty", got)
	}
}
