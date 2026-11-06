package security

import (
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

// rateLimitEntry 记录某个 IP 的请求窗口信息
type rateLimitEntry struct {
	count    int
	windowAt time.Time
}

// RateLimiter 基于 IP 的滑动窗口速率限制器
type RateLimiter struct {
	mu      sync.Mutex
	entries map[string]*rateLimitEntry
	limit   int           // 窗口内允许的最大请求数
	window  time.Duration // 窗口时长
}

// NewRateLimiter 创建速率限制器
func NewRateLimiter(limit int, window time.Duration) *RateLimiter {
	rl := &RateLimiter{
		entries: make(map[string]*rateLimitEntry),
		limit:   limit,
		window:  window,
	}
	// 后台定期清理过期条目，防止内存泄漏
	go rl.cleanup()
	return rl
}

// cleanup 每分钟清理一次过期条目
func (rl *RateLimiter) cleanup() {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()
	for range ticker.C {
		rl.mu.Lock()
		now := time.Now()
		for ip, entry := range rl.entries {
			if now.Sub(entry.windowAt) > rl.window {
				delete(rl.entries, ip)
			}
		}
		rl.mu.Unlock()
	}
}

// allow 检查指定 IP 是否允许通过
func (rl *RateLimiter) allow(ip string) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	entry, ok := rl.entries[ip]
	if !ok || now.Sub(entry.windowAt) > rl.window {
		rl.entries[ip] = &rateLimitEntry{count: 1, windowAt: now}
		return true
	}

	entry.count++
	return entry.count <= rl.limit
}

// RateLimitMiddleware 返回 Gin 中间件，对超限请求返回 429
//
// trustCFConnectingIP 打开时，限流键改用真实客户端 IP（见 EffectiveClientIP）：
// 默认关闭时键是对端 IP；由于本机的 tunnel/portproxy 转发会让所有外部请求都
// 呈现为 127.0.0.1，打开后外部用户才会各自拥有独立的桶。
func RateLimitMiddleware(rl *RateLimiter, trustCFConnectingIP bool) gin.HandlerFunc {
	return func(c *gin.Context) {
		ip := EffectiveClientIP(c, trustCFConnectingIP)
		if !rl.allow(ip) {
			c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
				"error": "rate limit exceeded, please try again later",
			})
			return
		}
		c.Next()
	}
}
