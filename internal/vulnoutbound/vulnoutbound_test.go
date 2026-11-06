package vulnoutbound

import (
	"strings"
	"testing"

	"jysecai/internal/database"
	"jysecai/internal/vulnmask"
)

// TestVulnerabilityPayloadMasksTitleAndTags 擋住「標題與標籤夾帶位址」的外洩路徑。
//
// 實測發現：生產資料的標題常夾帶真實位址
// （例：「三主機對本源 IP 52.128.238.210 返回一致的 403」），
// 而早期只遮 target/evidence/body，標題與 tag 欄位是整片漏掉的。
func TestVulnerabilityPayloadMasksTitleAndTags(t *testing.T) {
	v := &database.Vulnerability{
		ID:             "vuln-1",
		Title:          "三主機對本源 IP 52.128.238.210 返回一致的 403",
		Target:         "https://seo01.dlg8888.com/",
		Evidence:       "set-cookie: vsf-IPAddress=52.128.238.210%2C%2010.1.0.213",
		Description:    "回寫內網代理 10.1.0.213",
		ConversationTag: "目標 52.128.238.210",
		TaskTag:        "task 10.1.0.213",
		TypeRaw:        "IP 欺騙 / 內部網路資訊洩漏",
	}
	payload := VulnerabilityPayload(v, vulnmask.DefaultPolicy())
	blob := strings.Join([]string{
		payload.Title, payload.Target, payload.Evidence, payload.Body, payload.Meta,
	}, "\n")
	for _, leak := range []string{"52.128.238.210", "10.1.0.213"} {
		if strings.Contains(blob, leak) {
			t.Fatalf("位址 %s 未被遮蔽: %s", leak, blob)
		}
	}
}

// TestVulnerabilityPayloadKeepsAnalysisDimensions 確認分析維度沒有被遮掉。
func TestVulnerabilityPayloadKeepsAnalysisDimensions(t *testing.T) {
	v := &database.Vulnerability{
		ID:         "vuln-2",
		Type:       "SQL 注入",
		TypeCode:   "sql-injection",
		Severity:   "critical",
		Status:     "open",
		Confidence: 0,
	}
	payload := VulnerabilityPayload(v, vulnmask.DefaultPolicy())
	if payload.Category != "SQL 注入" || payload.TypeCode != "sql-injection" {
		t.Fatalf("分類不該被遮蔽: %+v", payload)
	}
	if payload.Severity != "critical" || payload.Status != "open" || payload.Confidence != 0 {
		t.Fatalf("嚴重度/狀態/信心值不該被遮蔽: %+v", payload)
	}
}
