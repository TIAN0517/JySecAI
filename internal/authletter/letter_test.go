package authletter

import (
	"encoding/json"
	"strings"
	"testing"
	"time"
)

// completeInput 一份事實齊全的授權書輸入。
func completeInput() Input {
	from := time.Date(2026, 11, 6, 0, 0, 0, 0, time.UTC)
	return Input{
		DocumentID:         "AUTH-2026-001",
		IssuedAt:           from,
		ClientName:         "示例股份有限公司",
		ClientTaxID:        "12345678",
		ClientAddress:      "台北市示例路 1 號",
		ClientApprover:     "王小明",
		ClientApproverRole: "資安長",
		ClientContact:      "02-0000-0000",
		VendorName:         "示例資安有限公司",
		VendorTaxID:        "87654321",
		VendorAddress:      "台北市測試路 2 號",
		VendorLead:         "李測試",
		ProjectID:          "proj-1",
		ProjectName:        "示例系統滲透測試",
		Objective:          "驗證對外服務的存取控制與輸入處理",
		Patterns:           []string{"app.example.com", "*.example.com", "10.20.0.0/24"},
		Operations:         []string{"passive_discovery", "active_scan", "exploit_validation"},
		ValidFrom:          from,
		ValidUntil:         from.AddDate(0, 0, 30),
		SourceAttested:     true,
	}
}

// TestBuildCompleteLetterIsQualified：事實齊全時應產生可簽署的授權書。
func TestBuildCompleteLetterIsQualified(t *testing.T) {
	result := Build(completeInput(), time.Date(2026, 11, 6, 0, 0, 0, 0, time.UTC))
	if !result.Qualified {
		t.Fatalf("事實齊全應為合格: gaps=%v", result.Gaps)
	}
	if !result.Attested {
		t.Fatal("已確認的授權事實應標示為 attested")
	}
	if result.DocumentID != "AUTH-2026-001" {
		t.Fatalf("文件編號應沿用授權編號: %q", result.DocumentID)
	}
	for _, needle := range []string{
		"資訊安全測試授權書",
		"示例股份有限公司",
		"王小明",
		"app.example.com",
		"*.example.com",
		"10.20.0.0/24",
		"利用驗證",
		"2026-11-06",
		"授權人簽名",
	} {
		if !strings.Contains(result.Markdown, needle) {
			t.Fatalf("Markdown 缺少內容: %q", needle)
		}
	}
	if !strings.Contains(result.HTML, "<html") || !strings.Contains(result.HTML, "資訊安全測試授權書") {
		t.Fatal("HTML 應是完整可列印文件")
	}
}

// TestBuildNeverInventsLegalFacts：沒有的事實不會被補上。
//
// 這是整個套件最核心的一條：產生器只排版，不發明法律事實。缺授權人就留白，
// 並且不可被標成 attested —— 否則平台就變成自己出具自己的授權憑據。
func TestBuildNeverInventsLegalFacts(t *testing.T) {
	in := completeInput()
	in.ClientApprover = ""
	in.ClientName = ""
	in.SourceAttested = false

	result := Build(in, time.Date(2026, 11, 6, 0, 0, 0, 0, time.UTC))
	if result.Qualified {
		t.Fatal("缺授權人與委託方時不應是合格文件")
	}
	if result.Attested {
		t.Fatal("未經人工確認的授權事實不應標示為 attested")
	}
	if result.Record.Attested {
		t.Fatal("機器可讀記錄也不應被標示為 attested")
	}
	if result.Record.ApprovedBy != "" {
		t.Fatalf("不應代填授權人: %q", result.Record.ApprovedBy)
	}
	if !strings.Contains(result.Markdown, "（待填）") {
		t.Fatal("缺的事實應在文件上留白")
	}
	if !strings.Contains(result.Markdown, "草稿") {
		t.Fatal("草稿狀態應明示於文件")
	}
	joined := strings.Join(result.Gaps, " ")
	for _, needle := range []string{"授權人", "甲方（委託方）名稱", "人工確認"} {
		if !strings.Contains(joined, needle) {
			t.Fatalf("缺口清單應說明缺什麼: %q / %v", needle, result.Gaps)
		}
	}
}

// TestBuildRejectsOverlongPeriod：授權期間上限與平台閘門一致（90 日）。
func TestBuildRejectsOverlongPeriod(t *testing.T) {
	in := completeInput()
	in.ValidUntil = in.ValidFrom.AddDate(0, 0, 120)
	result := Build(in, time.Now())
	if result.Qualified {
		t.Fatal("超過 90 日的授權不應是合格文件")
	}
	if !strings.Contains(strings.Join(result.Gaps, " "), "90 日上限") {
		t.Fatalf("缺口應說明超過上限: %v", result.Gaps)
	}
}

// TestBuildRejectsInvertedPeriod：結束時間早於開始時間。
func TestBuildRejectsInvertedPeriod(t *testing.T) {
	in := completeInput()
	in.ValidUntil = in.ValidFrom.AddDate(0, 0, -1)
	result := Build(in, time.Now())
	if result.Qualified {
		t.Fatal("結束時間早於開始時間時不應是合格文件")
	}
}

// TestRecordShapeMatchesPlatformAuthorization：機器可讀記錄必須能直接回填平台的授權欄位。
//
// 平台的 security_ops_runs.authorization_json 就是這個結構；形狀不一致的話，
// 產出的授權書就沒辦法變成平台自己認得的授權記錄。
func TestRecordShapeMatchesPlatformAuthorization(t *testing.T) {
	result := Build(completeInput(), time.Now())
	raw, err := RecordJSON(result.Record)
	if err != nil {
		t.Fatal(err)
	}
	var decoded map[string]any
	if err := json.Unmarshal([]byte(raw), &decoded); err != nil {
		t.Fatal(err)
	}
	for _, key := range []string{"id", "projectId", "targetPatterns", "operations", "validFrom", "validUntil", "approvedBy", "attested"} {
		if _, ok := decoded[key]; !ok {
			t.Fatalf("授權記錄缺少欄位 %q: %s", key, raw)
		}
	}
	if decoded["attested"] != true {
		t.Fatalf("已確認的記錄 attested 應為 true: %s", raw)
	}
	if decoded["approvedBy"] != "王小明" {
		t.Fatalf("授權人應沿用人工輸入值: %s", raw)
	}
}

// TestOperationsRenderedWithScope：授權模式要有中文名與範圍說明。
func TestOperationsRenderedWithScope(t *testing.T) {
	result := Build(completeInput(), time.Now())
	for _, needle := range []string{"被動偵察", "主動掃描", "利用驗證"} {
		if !strings.Contains(result.Markdown, needle) {
			t.Fatalf("Markdown 缺少操作模式說明: %q", needle)
		}
	}
}

// TestUnknownOperationIsFlagged：未定義的模式要標示出來讓甲方確認，而不是默默照印。
func TestUnknownOperationIsFlagged(t *testing.T) {
	in := completeInput()
	in.Operations = []string{"not_a_real_mode"}
	result := Build(in, time.Now())
	if !strings.Contains(result.Markdown, "未知模式") {
		t.Fatal("未知操作模式應在文件上標示")
	}
}

// TestSortedPatternsAreStable：範圍輸出順序固定，便於文件比對與稽核。
func TestSortedPatternsAreStable(t *testing.T) {
	in := completeInput()
	in.Patterns = []string{"z.example.com", "a.example.com", "m.example.com"}
	result := Build(in, time.Now())
	first := strings.Index(result.Markdown, "a.example.com")
	second := strings.Index(result.Markdown, "m.example.com")
	third := strings.Index(result.Markdown, "z.example.com")
	if first < 0 || second < 0 || third < 0 || !(first < second && second < third) {
		t.Fatalf("範圍應依排序輸出: %d %d %d", first, second, third)
	}
}

// TestHTMLBodyIsEmbeddable：HTMLBody 不含 html/head 外殼，且樣式收在 .letter 底下。
func TestHTMLBodyIsEmbeddable(t *testing.T) {
	result := Build(completeInput(), time.Now())
	if strings.Contains(result.HTMLBody, "<html") || strings.Contains(result.HTMLBody, "<head>") {
		t.Fatal("HTMLBody 不應含 html/head 外殼")
	}
	if strings.Contains(result.HTMLBody, "<style") {
		t.Fatal("樣式應由外層注入，HTMLBody 不應自帶 style")
	}
	if !strings.Contains(CSS, ".letter") {
		t.Fatal("授權書樣式應收在 .letter 底下，避免蓋掉報告排版")
	}
	for _, forbidden := range []string{"\nbody{", "\nh1{", "\ntable{", "\nfooter{"} {
		if strings.Contains(CSS, forbidden) {
			t.Fatalf("授權書樣式不應含頁面層級規則: %q", forbidden)
		}
	}
}
