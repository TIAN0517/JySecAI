package main

import (
	"strings"
	"testing"

	"jysecai/internal/config"
	"jysecai/internal/database"
)

func vuln(id, severity, target, repro, evidence string) *database.Vulnerability {
	return &database.Vulnerability{
		ID:         id,
		Severity:   severity,
		Target:     target,
		ReproSteps: repro,
		Evidence:   evidence,
	}
}

// TestUnverifiableReason 佔位殘留紀錄必須被擋下：target 是欄位名、target 空、
// 或沒有任何復現/證據，這三種送去複測只會換回一句「工具不可用」。
func TestUnverifiableReason(t *testing.T) {
	cases := []struct {
		name string
		v    *database.Vulnerability
		want string
	}{
		{"完整資料可派工", vuln("1", "high", "https://a.example.com/login", "1. go\n2. go", "resp 200"), ""},
		{"只有 URL 沒證據", vuln("2", "high", "https://a.example.com", "", ""), "無復現步驟與證據"},
		{"target 為空", vuln("3", "high", "   ", "1. go", "resp"), "target 為空"},
		{"target 是欄位名", vuln("4", "info", "target", "sql xss jwt", ""), "target 不像主機或 URL"},
		{"host:port 算目標", vuln("5", "medium", "a.example.com:443", "", "tls 憑證序號"), ""},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := unverifiableReason(tc.v); got != tc.want {
				t.Fatalf("unverifiableReason() = %q, want %q", got, tc.want)
			}
		})
	}
}

// TestSelectTargets_SeverityFirst 嚴重度排除必須在證據篩選之前生效，且兩者都要
// 記入 skipByReason——報告數字不對的話，使用者會誤以為篩選沒生效。
func TestSelectTargets_SeverityFirst(t *testing.T) {
	vulns := []*database.Vulnerability{
		vuln("keep-1", "high", "https://a.example.com", "repro", "evidence"),
		vuln("keep-2", "low", "b.example.com:80", "", "evidence"),
		vuln("crit-1", "critical", "https://c.example.com", "repro", "evidence"),
		vuln("junk-1", "info", "target", "", ""),
		vuln("junk-2", "low", "", "repro", ""),
	}
	picked, skipByReason, skipped := selectTargets(vulns, []string{"critical"}, true)

	if len(picked) != 2 {
		t.Fatalf("picked = %d 筆, want 2（%v）", len(picked), ids(picked))
	}
	if picked[0].ID != "keep-1" || picked[1].ID != "keep-2" {
		t.Fatalf("picked ids = %v, want [keep-1 keep-2]", ids(picked))
	}
	if len(skipped) != 3 {
		t.Fatalf("skipped = %d 筆, want 3", len(skipped))
	}
	if skipByReason["嚴重度被排除"] != 1 {
		t.Errorf("嚴重度被排除 = %d, want 1", skipByReason["嚴重度被排除"])
	}
	// junk-1 同時觸發兩條規則，只應記一次（target 不像主機先命中）。
	if got := skipByReason["target 不像主機或 URL"]; got != 1 {
		t.Errorf("target 不像主機或 URL = %d, want 1", got)
	}
	if got := skipByReason["target 為空"]; got != 1 {
		t.Errorf("target 為空 = %d, want 1", got)
	}
}

// TestSelectTargets_FilterDisabled --no-evidence-filter 應只擋嚴重度。
func TestSelectTargets_FilterDisabled(t *testing.T) {
	vulns := []*database.Vulnerability{
		vuln("junk-1", "info", "target", "", ""),
		vuln("crit-1", "critical", "https://c.example.com", "repro", "evidence"),
	}
	picked, skipByReason, _ := selectTargets(vulns, []string{"critical"}, false)
	if len(picked) != 1 || picked[0].ID != "junk-1" {
		t.Fatalf("picked = %v, want [junk-1]", ids(picked))
	}
	if skipByReason["嚴重度被排除"] != 1 {
		t.Errorf("嚴重度被排除 = %d, want 1", skipByReason["嚴重度被排除"])
	}
}

// TestNextBatch_SkipsDispatched 已派過的 id 不能再進下一批，否則複測失敗時會對同一
// 批漏洞無限重派。
func TestNextBatch_SkipsDispatched(t *testing.T) {
	picked := []*database.Vulnerability{
		vuln("a", "high", "https://a.example.com", "r", "e"),
		vuln("b", "high", "https://b.example.com", "r", "e"),
		vuln("c", "high", "https://c.example.com", "r", "e"),
	}
	dispatched := map[string]bool{"a": true, "b": true}

	tasks, ids := nextBatch(picked, dispatched, 10)
	if len(tasks) != 1 || len(ids) != 1 || ids[0] != "c" {
		t.Fatalf("ids = %v, want [c]", ids)
	}
	if tasks[0] == "" {
		t.Fatal("task message 為空")
	}
}

func TestNextBatch_RespectsBatchSize(t *testing.T) {
	picked := []*database.Vulnerability{
		vuln("a", "high", "https://a.example.com", "r", "e"),
		vuln("b", "high", "https://b.example.com", "r", "e"),
		vuln("c", "high", "https://c.example.com", "r", "e"),
	}
	_, ids := nextBatch(picked, map[string]bool{}, 2)
	if len(ids) != 2 || ids[0] != "a" || ids[1] != "b" {
		t.Fatalf("ids = %v, want [a b]", ids)
	}
}

// TestNextBatch_UsesSharedPrompt 提示詞必須來自 handler.BuildAutoVerifyPrompt：
// 那段文字帶著全部安全邊界（唯讀、禁用 c2_*/webshell_*、必須寫回），drain 自己
// 寫一份等於把邊界分裂成兩份。
func TestNextBatch_UsesSharedPrompt(t *testing.T) {
	v := vuln("deadbeef-0000", "high", "https://a.example.com", "repro steps", "evidence body")
	tasks, _ := nextBatch([]*database.Vulnerability{v}, map[string]bool{}, 1)
	if len(tasks) != 1 {
		t.Fatalf("tasks = %d, want 1", len(tasks))
	}
	for _, must := range []string{"deadbeef-0000", "update_vulnerability", "只做讀取式驗證", "禁止呼叫 c2_*", "tool_search"} {
		if !strings.Contains(tasks[0], must) {
			t.Errorf("任務訊息缺少 %q", must)
		}
	}
}

// TestDeriveBaseURL_WildcardHostBecomesLoopback 伺服器綁 0.0.0.0 時不能照抄成
// base-url——0.0.0.0 不是可連線的目標。
func TestDeriveBaseURL_WildcardHostBecomesLoopback(t *testing.T) {
	cases := []struct {
		name string
		cfg  config.Config
		want string
	}{
		{"0.0.0.0 + TLS 走回環", config.Config{Server: config.ServerConfig{Host: "0.0.0.0", Port: 8855, TLSEnabled: true}}, "https://127.0.0.1:8855"},
		{"空 host 走回環", config.Config{Server: config.ServerConfig{Port: 8080}}, "http://127.0.0.1:8080"},
		{"具體 host 保留", config.Config{Server: config.ServerConfig{Host: "10.0.0.5", Port: 8855, TLSEnabled: true}}, "https://10.0.0.5:8855"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := deriveBaseURL(&tc.cfg); got != tc.want {
				t.Fatalf("deriveBaseURL() = %q, want %q", got, tc.want)
			}
		})
	}
}

// TestIsLoopbackHost --insecure 只允許回環位址：伺服器對外也開同一個 port，
// 遠端連線關掉憑證驗證等於把 token 交給中間人。
func TestIsLoopbackHost(t *testing.T) {
	cases := map[string]bool{
		"127.0.0.1":           true,
		"localhost":           true,
		"::1":                 true,
		"192.168.1.10":        false,
		"jysecai.example.com": false,
	}
	for host, want := range cases {
		if got := isLoopbackHost(host); got != want {
			t.Errorf("isLoopbackHost(%q) = %v, want %v", host, got, want)
		}
	}
}

func ids(vulns []*database.Vulnerability) []string {
	out := make([]string, 0, len(vulns))
	for _, v := range vulns {
		out = append(out, v.ID)
	}
	return out
}
