package xsstemplates

import (
	"bytes"
	"strings"
	"testing"
	"text/template"
)

// parseAll 確認全部模板語法有效。模板是 embed 進來的字串，編譯期不會被
// 檢查，壞掉的模板只會在 payload 服務時爆炸 —— 所以在測試裡先炸。
func parseAll(t *testing.T) *template.Template {
	t.Helper()
	tpl, err := template.ParseFS(FS, "*.js.tmpl")
	if err != nil {
		t.Fatalf("模板解析失敗: %v", err)
	}
	return tpl
}

type vars struct {
	Token              string
	ProjectID          string
	CaptureBase        string
	BeaconBase         string
	MaxBytes           int
	KeepSessionSeconds int
	Html2CanvasURL     string
	FormHookNoMask     bool
}

func sampleVars() vars {
	return vars{
		Token:              "tok-123",
		ProjectID:          "proj-1",
		CaptureBase:        "https://collector.example",
		BeaconBase:         "https://collector.example",
		MaxBytes:           4096,
		KeepSessionSeconds: 30,
		Html2CanvasURL:     "/vendor/html2canvas-1.4.1.min.js",
		FormHookNoMask:     false,
	}
}

func TestAllTemplatesRender(t *testing.T) {
	tpl := parseAll(t)
	for _, m := range Registry {
		var buf bytes.Buffer
		if err := tpl.ExecuteTemplate(&buf, m.Name+".js.tmpl", sampleVars()); err != nil {
			t.Errorf("模組 %s 渲染失敗: %v", m.Name, err)
			continue
		}
		out := buf.String()
		if !strings.Contains(out, "tok-123") {
			t.Errorf("模組 %s 輸出未含 token", m.Name)
		}
		if strings.Contains(out, "{{") {
			t.Errorf("模組 %s 輸出殘留未展開的模板語法", m.Name)
		}
	}
}

// TestCookieOnlyInFullcookie 是這個模組庫最重要的不變量：除了 fullcookie，
// 任何模板都不得出現 document.cookie 的實際取用。這是 xss.go 頂部
// 「never collects session cookies」承諾在 payload 側的對應檢查。
func TestCookieOnlyInFullcookie(t *testing.T) {
	tpl := parseAll(t)
	for _, m := range Registry {
		var buf bytes.Buffer
		if err := tpl.ExecuteTemplate(&buf, m.Name+".js.tmpl", sampleVars()); err != nil {
			continue
		}
		has := strings.Contains(buf.String(), "document.cookie")
		if m.Name == "fullcookie" && !has {
			t.Error("fullcookie 模組反而沒有取用 document.cookie")
		}
		if m.Name != "fullcookie" && has {
			t.Errorf("模組 %s 取用了 document.cookie，違反 canary-only 邊界", m.Name)
		}
	}
}

// TestNoDynamicCodeLoading：移植時刻意砍掉 chainload 機制，任何模板都
// 不得出現 eval / new Function / 遠端 script 注入（screenshot 的 LIB 是
// 固定的 vendor 路徑，且由 renderCollectorJS 注入，不是執行期字串拼接）。
func TestNoDynamicCodeLoading(t *testing.T) {
	tpl := parseAll(t)
	for _, m := range Registry {
		var buf bytes.Buffer
		if err := tpl.ExecuteTemplate(&buf, m.Name+".js.tmpl", sampleVars()); err != nil {
			continue
		}
		out := buf.String()
		for _, bad := range []string{"eval(", "new Function", "chainload"} {
			if strings.Contains(out, bad) {
				t.Errorf("模組 %s 含動態執行痕跡 %q", m.Name, bad)
			}
		}
	}
}

func TestValidateName(t *testing.T) {
	if !ValidateName("metadata") {
		t.Error("metadata 應為合法模組")
	}
	if ValidateName("../../etc/passwd") || ValidateName("") {
		t.Error("任意檔名不應通過驗證")
	}
}

// TestSensitiveFlags 鎖住敏感模組的註冊狀態：這兩支一旦被誤改成預設
// 啟用，等於繞過 HITL 邊界，所以這裡直接寫死。
func TestSensitiveFlags(t *testing.T) {
	for _, m := range Registry {
		switch m.Name {
		case "formhook", "fullcookie":
			if !m.Sensitive || m.DefaultEnabled {
				t.Errorf("敏感模組 %s 必須 Sensitive=true 且 DefaultEnabled=false", m.Name)
			}
		default:
			if m.Sensitive {
				t.Errorf("非敏感模組 %s 不應標記 Sensitive", m.Name)
			}
		}
	}
}
