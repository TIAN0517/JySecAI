package security

import (
	"github.com/gin-gonic/gin"
)

// ConsoleCSP 是管理主控台（Web UI）適用的 Content-Security-Policy。
//
// 為什麼要加這一道：認證 token 只存在 localStorage，任何能在主控台同源下
// 執行的 JavaScript 都能直接把它讀走 —— 公開審計揭露過的同型儲存型 XSS
// 就是這樣一路變成 C2 主控端 RCE 的。XSS 的根因修掉之後，CSP 是第二道
// 防線：就算日後又有人寫出一個注入點，script-src 也會擋掉「從外部網域
// 載入 <script src>」這個攻擊鏈裡最關鍵的一步。
//
// script-src 保留 'unsafe-inline'：現有主控台大量使用 inline onclick=
// 事件屬性，全面改寫成事件委派不在本次範圍內。'self' 仍能擋掉外部來源
// 的腳本載入 —— 這正是需要擋的那一步。
//
// index.html 與 web/static/css 都沒有任何外部 CDN 資源（只有一個外部
// <a href> 連結），所以這組政策不會擋掉任何正常功能。
//
// img-src 保留 https:：漏洞清單會顯示被掃目標的網站圖示，那來自外部網域。
const ConsoleCSP = "default-src 'self'; " +
	"script-src 'self' 'unsafe-inline'; " +
	"style-src 'self' 'unsafe-inline'; " +
	"img-src 'self' data: blob: https:; " +
	"font-src 'self' data:; " +
	"connect-src 'self' https: wss:; " +
	"media-src 'self' blob:; " +
	"object-src 'none'; " +
	"base-uri 'self'; " +
	"form-action 'self' https:; " +
	"frame-ancestors 'self'"

// CSPMiddleware 替所有回應加上 Content-Security-Policy 與基礎安全標頭。
//
// 已經帶有 CSP 的回應（例如 XSS collector 的 default-src 'none'）不被覆寫 ——
// 那條路徑自己設了更嚴格的政策，不該被這裡降級。
//
// X-Frame-Options 是給沒有支援 frame-ancestors 的老瀏覽器補的；
// Referrer-Policy 用 no-referrer，避免路徑／查詢參數外洩到外部站台。
func CSPMiddleware(policy string) gin.HandlerFunc {
	return func(c *gin.Context) {
		h := c.Writer.Header()
		if policy != "" && h.Get("Content-Security-Policy") == "" {
			h.Set("Content-Security-Policy", policy)
		}
		if h.Get("X-Content-Type-Options") == "" {
			h.Set("X-Content-Type-Options", "nosniff")
		}
		if h.Get("X-Frame-Options") == "" {
			h.Set("X-Frame-Options", "SAMEORIGIN")
		}
		if h.Get("Referrer-Policy") == "" {
			h.Set("Referrer-Policy", "no-referrer")
		}
		c.Next()
	}
}
