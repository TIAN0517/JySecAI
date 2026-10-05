// Package xsstemplates 內嵌 XSS payload 模組模板。
//
// 每支模組是自包含的 IIFE（GO text/template），渲染後直接可由 collector
// 服務。刻意不做成 2020 平台那種「多模組串接同一個 scope」——那是模組
// 互相衝突與 chainload 遠端第二段的溫床；這裡的模組清單在 payload 建立
// 時就固定，不留任何執行期動態載入。
//
// 模板變數（由 renderCollectorJS 注入）：
//
//	.Token            payload token（現有 XssPayload.Token）
//	.ProjectID        歸屬專案
//	.CaptureBase      capture 端點基底（publicBaseURL + "/xss/capture"）
//	.BeaconBase       GIF beacon 端點基底
//	.MaxBytes         單次上傳上限（與伺服器 XssMaxCaptureBytes 一致）
//
// 安全邊界（與 internal/handler/xss.go 頂部註解一致）：
//   - metadata / screenshot / keepsession 一律不讀 document.cookie；
//   - fullcookie / formhook 屬敏感模組：payload 建立時必須顯式勾選，
//     且 arming 走 HITL 核准，稽核單獨署名。
package xsstemplates

import "embed"

// FS 內嵌全部模組模板。
//
//go:embed *.js.tmpl README.md
var FS embed.FS

// Module 描述一支模組的註冊資訊。
type Module struct {
	// Name 是模板檔名（不含 .js.tmpl）與 capture kind 字串。
	Name string
	// Title / Description 供管理介面與稽核報告顯示。
	Title string
	// Sensitive 為 true 時：payload 建立需顯式勾選，arming 需 HITL 核准。
	Sensitive bool
	// DefaultEnabled 是新 payload 的預設勾選狀態。
	DefaultEnabled bool
}

// Registry 是全部可用模組。順序即管理介面顯示順序。
var Registry = []Module{
	{Name: "metadata", Title: "基本資訊", DefaultEnabled: true},
	{Name: "screenshot", Title: "頁面截圖", DefaultEnabled: true},
	{Name: "keepsession", Title: "Keep-session 心跳", DefaultEnabled: true},
	{Name: "formhook", Title: "表單攔截", Sensitive: true},
	{Name: "fullcookie", Title: "完整 Cookie", Sensitive: true},
}

// ValidateName 確認模組名稱存在，避免任意檔名注入 embed 查找。
func ValidateName(name string) bool {
	for _, m := range Registry {
		if m.Name == name {
			return true
		}
	}
	return false
}
