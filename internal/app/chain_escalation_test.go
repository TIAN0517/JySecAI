package app

import (
	"strings"
	"testing"
)

// chainStepFixture 造一個有證據的鏈環節。
func chainStepFixture(id, title, severity string, confidence int) ChainStep {
	return ChainStep{
		ID:         id,
		Title:      title,
		Severity:   severity,
		Confidence: confidence,
		Type:       "資訊洩漏",
		TypeRaw:    "資訊洩漏",
		Target:     "https://app.example.com",
		Evidence:   "GET /export -> 200 with full customer table",
		ReproSteps: "1. GET /export with admin cookie",
	}
}

// TestBuildChainRequiresTwoSteps：少於兩環不算鏈。
func TestBuildChainRequiresTwoSteps(t *testing.T) {
	_, err := buildChainVulnerability(ChainInput{
		Steps:  []ChainStep{chainStepFixture("v1", "單點", "medium", 95)},
		Impact: "可取得資料",
	})
	if err == nil {
		t.Fatal("單環不應該被當成攻擊鏈")
	}
	if !strings.Contains(err.Error(), "至少需要 2 個環節") {
		t.Fatalf("錯誤訊息應說明環節數不足: %v", err)
	}
}

// TestBuildChainRejectsStepWithoutEvidence：缺證據的環節讓整條鏈不成立。
//
// 這是鏈與單點發現最大的差別：鏈的結論是「這些環節串得起來」，只要有一環沒被證實，
// 串起來的說法就沒有根據。放行會讓一份沒有根據的結論進到交付報告裡。
func TestBuildChainRejectsStepWithoutEvidence(t *testing.T) {
	step := chainStepFixture("v2", "無證據環節", "high", 95)
	step.Evidence = ""
	_, err := buildChainVulnerability(ChainInput{
		Steps:  []ChainStep{chainStepFixture("v1", "資訊洩漏", "medium", 95), step},
		Impact: "可取得資料",
	})
	if err == nil {
		t.Fatal("缺證據的環節不應該組成攻擊鏈")
	}
	if !strings.Contains(err.Error(), "沒有證據") {
		t.Fatalf("錯誤訊息應指出缺證據: %v", err)
	}
}

// TestBuildChainConfidenceTakesWeakestLink：置信度取最弱環節。
func TestBuildChainConfidenceTakesWeakestLink(t *testing.T) {
	chain, err := buildChainVulnerability(ChainInput{
		Steps: []ChainStep{
			chainStepFixture("v1", "資訊洩漏", "medium", 98),
			chainStepFixture("v2", "越權存取", "high", 70),
		},
		Impact: "可讀取全量客戶資料",
	})
	if err != nil {
		t.Fatal(err)
	}
	if chain.Confidence != 70 {
		t.Fatalf("置信度應取最弱環節 70，實際 %d", chain.Confidence)
	}
	// 70 < 95，狀態不能是 confirmed。
	if chain.Status == "confirmed" {
		t.Fatal("鏈的置信度未達門檻，狀態不能是 confirmed")
	}
}

// TestBuildChainEscalatesToCriticalOnHighImpact：中危單點串成接管鏈時應升級為 critical。
//
// 這是「嚴重漏洞自動產出」的核心：單看每一條都是中危，串起來能接管 —— 報告裡如果
// 只有三條中危，委託方排不出優先順序。
func TestBuildChainEscalatesToCriticalOnHighImpact(t *testing.T) {
	chain, err := buildChainVulnerability(ChainInput{
		Steps: []ChainStep{
			chainStepFixture("v1", "資訊洩漏", "medium", 96),
			chainStepFixture("v2", "未授權後台", "medium", 96),
		},
		Impact: "可取得後台管理員 Session 並接管整個後台",
	})
	if err != nil {
		t.Fatal(err)
	}
	if chain.Severity != "critical" {
		t.Fatalf("接管類的鏈應升為 critical，實際 %q", chain.Severity)
	}
	if chain.Confidence != 96 {
		t.Fatalf("置信度應為 96，實際 %d", chain.Confidence)
	}
	if chain.Status != "confirmed" {
		t.Fatalf("置信度達標應為 confirmed，實際 %q", chain.Status)
	}
	if !strings.Contains(chain.Title, "攻擊鏈") {
		t.Fatalf("標題應標示為攻擊鏈: %q", chain.Title)
	}
	if !strings.Contains(chain.Evidence, "v1") || !strings.Contains(chain.Evidence, "v2") {
		t.Fatal("證據應列出各環節的來源漏洞 ID")
	}
	if !strings.Contains(chain.Impact, "接管") {
		t.Fatalf("影響說明應保留: %q", chain.Impact)
	}
}

// TestBuildChainKeepsSeverityWhenImpactIsBenign：後果不嚴重時不該硬升級。
func TestBuildChainKeepsSeverityWhenImpactIsBenign(t *testing.T) {
	chain, err := buildChainVulnerability(ChainInput{
		Steps: []ChainStep{
			chainStepFixture("v1", "資訊洩漏", "medium", 96),
			chainStepFixture("v2", "錯誤訊息洩漏", "low", 96),
		},
		Impact: "可得知內部版本號碼",
	})
	if err != nil {
		t.Fatal(err)
	}
	if chain.Severity != "medium" {
		t.Fatalf("後果輕微時應維持 medium，實際 %q", chain.Severity)
	}
}

// TestChainImpactImpliesCritical：影響特徵的判定要有涵蓋率也別太寬。
func TestChainImpactImpliesCritical(t *testing.T) {
	for _, impact := range []string{
		"可取得遠端代碼執行能力",
		"可讀寫任意檔案",
		"可接管帳號",
		"造成資料外洩",
		"跨租戶讀取訂單",
	} {
		if !chainImpactImpliesCritical(impact) {
			t.Fatalf("應判定為 critical 影響: %q", impact)
		}
	}
	for _, impact := range []string{
		"可得知內部版本號碼",
		"可取得說明文件",
		"",
	} {
		if chainImpactImpliesCritical(impact) {
			t.Fatalf("不應判定為 critical 影響: %q", impact)
		}
	}
}
