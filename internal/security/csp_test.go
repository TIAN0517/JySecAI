package security

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/gin-gonic/gin"
)

func TestCSPMiddlewareSetsPolicyAndHeaders(t *testing.T) {
	gin.SetMode(gin.TestMode)
	router := gin.New()
	router.Use(CSPMiddleware(ConsoleCSP))
	router.GET("/", func(c *gin.Context) { c.String(http.StatusOK, "ok") })

	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/", nil))

	policy := recorder.Header().Get("Content-Security-Policy")
	if policy == "" {
		t.Fatal("Content-Security-Policy 未設定")
	}
	// script-src 'self' 是這道防線的核心：擋掉「從外部網域載入 <script src>」。
	for _, want := range []string{
		"script-src 'self'",
		"object-src 'none'",
		"base-uri 'self'",
		"frame-ancestors 'self'",
	} {
		if !strings.Contains(policy, want) {
			t.Fatalf("CSP 缺少 %q：%s", want, policy)
		}
	}
	if recorder.Header().Get("X-Content-Type-Options") != "nosniff" {
		t.Fatal("X-Content-Type-Options 應為 nosniff")
	}
	if recorder.Header().Get("X-Frame-Options") != "SAMEORIGIN" {
		t.Fatal("X-Frame-Options 應為 SAMEORIGIN")
	}
	if recorder.Header().Get("Referrer-Policy") != "no-referrer" {
		t.Fatal("Referrer-Policy 應為 no-referrer")
	}
}

func TestCSPMiddlewareDoesNotOverrideExistingPolicy(t *testing.T) {
	gin.SetMode(gin.TestMode)
	router := gin.New()
	router.Use(CSPMiddleware(ConsoleCSP))
	// XSS collector 端點自己設了更嚴格的 default-src 'none'，不能被降級。
	router.GET("/collector", func(c *gin.Context) {
		c.Header("Content-Security-Policy", "default-src 'none'")
		c.String(http.StatusOK, "ok")
	})

	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/collector", nil))

	if got := recorder.Header().Get("Content-Security-Policy"); got != "default-src 'none'" {
		t.Fatalf("既有的 CSP 被覆寫了：%s", got)
	}
}

func TestCSPMiddlewareEmptyPolicyKeepsHandlerOwnHeaders(t *testing.T) {
	gin.SetMode(gin.TestMode)
	router := gin.New()
	router.Use(CSPMiddleware(""))
	router.GET("/", func(c *gin.Context) { c.String(http.StatusOK, "ok") })

	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/", nil))

	if got := recorder.Header().Get("Content-Security-Policy"); got != "" {
		t.Fatalf("空政策不該設定 CSP：%s", got)
	}
	// 安全標頭仍然要加。
	if recorder.Header().Get("X-Content-Type-Options") != "nosniff" {
		t.Fatal("X-Content-Type-Options 應為 nosniff")
	}
}
