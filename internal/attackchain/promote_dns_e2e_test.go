package attackchain

import (
	"path/filepath"
	"strings"
	"testing"

	"jysecai/internal/database"

	"go.uber.org/zap"
)

// 這是「創建名一律為目標 DNS」的端到端驗證：
// 從對話裡的漏洞（實際下過手的目標）一路走到專案事實落庫，
// 確認建立的名全部掛在目標 DNS 下，而且真的寫進了資料庫。
//
// 只測 allocatePromoteFactKey 不夠 —— 命名規則再對，沒入庫也等於沒做。

func newPromoteE2ETestDB(t *testing.T) (*database.DB, string, string) {
	t.Helper()
	db, err := database.NewDB(filepath.Join(t.TempDir(), "promote-e2e.db"), zap.NewNop())
	if err != nil {
		t.Fatalf("NewDB: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })

	project, err := db.CreateProject(&database.Project{Name: "e2e project"})
	if err != nil {
		t.Fatalf("CreateProject: %v", err)
	}
	conv, err := db.CreateConversation("e2e conversation", database.ConversationCreateMeta{})
	if err != nil {
		t.Fatalf("CreateConversation: %v", err)
	}
	return db, project.ID, conv.ID
}

func TestPromoteToProjectNamesEverythingByTargetDNS(t *testing.T) {
	db, projectID, convID := newPromoteE2ETestDB(t)

	// 1) 掃描階段留下的漏洞：目標是實際下過手的網址。
	if _, err := db.CreateVulnerability(&database.Vulnerability{
		ConversationID: convID,
		Title:          "login SQL 注入",
		Description:    "登入參數可注入",
		Severity:       "high",
		Status:         database.VulnerabilityStatusConfirmed,
		Confidence:     97,
		Type:           "SQL注入",
		Target:         "https://api.example.com/v1/login",
		Evidence:       "差異回應已驗證",
	}); err != nil {
		t.Fatalf("CreateVulnerability: %v", err)
	}

	// 2) 攻擊鏈：目標 → 發現 → 利用動作。
	if err := db.SaveAttackChainNode(convID, "n-target", "target", "api.example.com", "", "", 0); err != nil {
		t.Fatalf("SaveAttackChainNode target: %v", err)
	}
	if err := db.SaveAttackChainNode(convID, "n-find", "vulnerability", "login SQL 注入", "", "", 80); err != nil {
		t.Fatalf("SaveAttackChainNode finding: %v", err)
	}
	if err := db.SaveAttackChainNode(convID, "n-act", "action", "dump database credentials", "", "", 60); err != nil {
		t.Fatalf("SaveAttackChainNode action: %v", err)
	}
	if err := db.SaveAttackChainEdge(convID, "e1", "n-target", "n-find", "discovers", 1); err != nil {
		t.Fatalf("SaveAttackChainEdge: %v", err)
	}
	if err := db.SaveAttackChainEdge(convID, "e2", "n-find", "n-act", "exploits", 1); err != nil {
		t.Fatalf("SaveAttackChainEdge: %v", err)
	}

	// 3) 沉淀成專案事實。
	res, err := PromoteToProject(db, projectID, convID)
	if err != nil {
		t.Fatalf("PromoteToProject: %v", err)
	}
	if res.TargetDNS != "api.example.com" {
		t.Fatalf("目標 DNS 解析錯誤: %q, want api.example.com", res.TargetDNS)
	}
	if res.FactsCreated != 3 {
		t.Fatalf("應建立 3 筆事實，實際 %d (keys=%v)", res.FactsCreated, res.FactKeys)
	}

	// 4) 每個名都要掛在目標 DNS 下。
	for _, key := range res.FactKeys {
		if !strings.Contains(key, "api.example.com") {
			t.Fatalf("事實名未掛目標 DNS: %q", key)
		}
	}

	// 5) 真的入庫了 —— 命名對但沒寫進去，等於沒做。
	for _, key := range res.FactKeys {
		fact, err := db.GetProjectFactByKey(projectID, key)
		if err != nil {
			t.Fatalf("事實 %q 沒入庫: %v", key, err)
		}
		if fact == nil || fact.FactKey != key {
			t.Fatalf("事實 %q 內容不符: %+v", key, fact)
		}
	}

	// 6) 目標事實的 key 就是 DNS 本身。
	if _, err := db.GetProjectFactByKey(projectID, "target/api.example.com"); err != nil {
		t.Fatalf("目標事實未以 DNS 命名: %v", err)
	}
}

// TestPromoteToProjectFallsBackWhenNoDNSResolvable 沒有 DNS 時不能失敗 ——
// 命名不統一是問題，寫不進資料是更大的問題。
func TestPromoteToProjectFallsBackWhenNoDNSResolvable(t *testing.T) {
	db, projectID, convID := newPromoteE2ETestDB(t)

	// 目標是 IP，沒有可穩定引用的 DNS。
	if _, err := db.CreateVulnerability(&database.Vulnerability{
		ConversationID: convID,
		Title:          "internal service exposure",
		Severity:       "medium",
		Status:         database.VulnerabilityStatusOpen,
		Type:           "資訊洩漏",
		Target:         "192.168.1.10:8080",
	}); err != nil {
		t.Fatalf("CreateVulnerability: %v", err)
	}
	if err := db.SaveAttackChainNode(convID, "n-find", "vulnerability", "internal service exposure", "", "", 10); err != nil {
		t.Fatalf("SaveAttackChainNode: %v", err)
	}

	res, err := PromoteToProject(db, projectID, convID)
	if err != nil {
		t.Fatalf("PromoteToProject 不該因為沒有 DNS 而失敗: %v", err)
	}
	if res.FactsCreated != 1 {
		t.Fatalf("應建立 1 筆事實，實際 %d", res.FactsCreated)
	}
	if res.TargetDNS != "" {
		t.Fatalf("IP 不該被當成 DNS: %q", res.TargetDNS)
	}
	if _, err := db.GetProjectFactByKey(projectID, res.FactKeys[0]); err != nil {
		t.Fatalf("退回命名後仍應入庫: %v", err)
	}
}
