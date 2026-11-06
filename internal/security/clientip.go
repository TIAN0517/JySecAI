package security

import (
	"net"
	"strings"

	"github.com/gin-gonic/gin"
)

// EffectiveClientIP 回傳用於限流與稽核的「真實客戶端 IP」。
//
// 為什麼需要這一層：這台機器上，Windows→WSL 的 localhost 轉發與 Cloudflare
// tunnel 進來的請求，在核心看到的對端 IP 全是 127.0.0.1（實測確認）。若直接
// 拿 c.ClientIP() 當限流鍵，所有外部使用者會共用同一個桶——外部只要打滿
// 10 次/分，整站登入（含主控台）會一起被鎖死，等於一個免費的 DoS。
//
// 解法是讓「真正知道客戶端 IP 的那一層」把 IP 寫進一個「保證會被覆寫」的標頭：
//   · Cloudflare 邊緣會覆寫 CF-Connecting-IP（tunnel 路徑）。
//   · 自建反代必須在 proxy 層覆寫，不得透傳客戶端自帶的值。
//
// 因此這裡只在 (a) 設定明確開啟、且 (b) 對端是 loopback 時才採信該標頭。
// 對端不是 loopback 時一律用 socket 對端位址——外部攻擊者連不到本機的
// loopback，也就不可能偽造。
func EffectiveClientIP(c *gin.Context, trustCFConnectingIP bool) string {
	if c == nil {
		return ""
	}
	peer := strings.TrimSpace(c.ClientIP())
	if !trustCFConnectingIP || !isLoopbackIP(peer) {
		return peer
	}
	forwarded := strings.TrimSpace(c.GetHeader("CF-Connecting-IP"))
	if forwarded == "" || net.ParseIP(forwarded) == nil {
		return peer
	}
	return forwarded
}

// isLoopbackIP 判斷字串是否為 loopback 位址（127.0.0.0/8 或 ::1）。
func isLoopbackIP(ip string) bool {
	parsed := net.ParseIP(strings.TrimSpace(ip))
	if parsed == nil {
		return false
	}
	return parsed.IsLoopback()
}
