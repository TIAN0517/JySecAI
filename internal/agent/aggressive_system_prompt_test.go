package agent

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"jysecai/internal/config"

	"go.uber.org/zap"
)

// TestEinoSingleAgentSystemInstructionUsesPreset：設定檔的 preset 真的會進到系統提示。
//
// 只測純函式不夠 —— 這裡測的是「設定 → 系統提示」整條接線，避免改了設定卻沒生效。
func TestEinoSingleAgentSystemInstructionUsesPreset(t *testing.T) {
	agent := &Agent{
		agentConfig: &config.AgentConfig{SystemPromptPreset: config.SystemPromptPresetAggressive},
		logger:      zap.NewNop(),
	}
	prompt := agent.EinoSingleAgentSystemInstruction()
	if !strings.Contains(prompt, "進攻型滲透測試作戰代理") {
		t.Fatalf("aggressive preset 未生效:\n%s", prompt[:min(300, len(prompt))])
	}

	agent.agentConfig = &config.AgentConfig{}
	prompt = agent.EinoSingleAgentSystemInstruction()
	if !strings.Contains(prompt, "安全研究助手") {
		t.Fatalf("未設定 preset 時應使用 default:\n%s", prompt[:min(300, len(prompt))])
	}
}

// TestEinoSingleAgentSystemInstructionFileOverridesPreset：system_prompt_path 優先於 preset。
//
// 檔案是操作者手寫的最後一道覆寫，優先級最高。
func TestEinoSingleAgentSystemInstructionFileOverridesPreset(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "custom.md")
	if err := os.WriteFile(path, []byte("自訂提示詞"), 0o600); err != nil {
		t.Fatal(err)
	}
	agent := &Agent{
		agentConfig: &config.AgentConfig{
			SystemPromptPreset: config.SystemPromptPresetAggressive,
			SystemPromptPath:   path,
		},
		promptBaseDir: dir,
		logger:        zap.NewNop(),
	}
	if prompt := agent.EinoSingleAgentSystemInstruction(); prompt != "自訂提示詞" {
		t.Fatalf("檔案應覆蓋 preset，實際: %q", prompt)
	}
}

// TestSingleAgentSystemPromptForPresetFallback：未知 preset 必須回退 default。
//
// 理由：設定檔打錯字時靜默換成進攻型（或反過來）是看不出來的事 —— 平台會在沒有
// 任何人察覺的情況下換掉 Agent 的行為。回退到預設是安全的那一側。
func TestSingleAgentSystemPromptForPresetFallback(t *testing.T) {
	unknown := SingleAgentSystemPromptForPreset("agressive") // 拼字錯誤
	if unknown != DefaultSingleAgentSystemPrompt() {
		t.Fatal("未知 preset 應回退 default")
	}
	if empty := SingleAgentSystemPromptForPreset(""); empty != DefaultSingleAgentSystemPrompt() {
		t.Fatal("空 preset 應回退 default")
	}
	if aggressive := SingleAgentSystemPromptForPreset(config.SystemPromptPresetAggressive); aggressive != AggressiveSingleAgentSystemPrompt() {
		t.Fatal("aggressive preset 應回傳進攻型提示")
	}
	if aggressive := SingleAgentSystemPromptForPreset("AGGRESSIVE"); aggressive != AggressiveSingleAgentSystemPrompt() {
		t.Fatal("preset 名稱應大小寫不拘")
	}
}

// TestAggressivePromptKeepsHardDiscipline：進攻型提示必須保留三條硬紀律。
//
// 進攻不等於沒有底線。這三條一旦從提示裡消失，平台就會開始產生沒有證據的結論，
// 那正是交付物最不能出錯的地方。
func TestAggressivePromptKeepsHardDiscipline(t *testing.T) {
	prompt := AggressiveSingleAgentSystemPrompt()
	for _, needle := range []string{
		"不要編造判定結果",
		"不偽造工具執行紀錄",
		"命中就停",
	} {
		if !strings.Contains(prompt, needle) {
			t.Fatalf("進攻型提示缺少硬紀律: %q", needle)
		}
	}
}

// TestAggressivePromptRemovesSelfCensorship：進攻型提示不能帶著保守預設的自我審查條款。
//
// 這幾條是 default 提示裡讓 Agent 在程式層沒擋時還自己擋一次的來源；換了 preset
// 卻沒換掉它，preset 就只是個開關名稱。
func TestAggressivePromptRemovesSelfCensorship(t *testing.T) {
	prompt := AggressiveSingleAgentSystemPrompt()
	for _, needle := range []string{
		"优先使用只读、低影响方式",
		"不协助凭据窃取、隐蔽持久化、破坏数据",
		"不得通过换入口、换工具或修改参数绕过同一安全限制",
		"不自动扩大目标范围、提升扫描强度",
	} {
		if strings.Contains(prompt, needle) {
			t.Fatalf("進攻型提示仍帶著保守條款: %q", needle)
		}
	}
}

// TestAggressivePromptAlignsWithPentestDoctrine：進攻型提示要寫出攻擊紀律本身。
func TestAggressivePromptAlignsWithPentestDoctrine(t *testing.T) {
	prompt := AggressiveSingleAgentSystemPrompt()
	for _, needle := range []string{
		"深度優先打穿",
		"拿到憑據即擴散",
		"自動升級強度",
		"被擋就換路",
		"立即",
		"escalate_findings_chain",
		"record_vulnerability",
		"undetermined",
		"目標端的防禦繞過屬於評估技術",
	} {
		if !strings.Contains(prompt, needle) {
			t.Fatalf("進攻型提示缺少攻擊紀律: %q", needle)
		}
	}
}

// TestDefaultPromptUnchanged：default 提示不該被進攻型改動波及。
//
// 預設行為變更是最難察覺的回歸 —— 整個平台的對話品質都靠它。
func TestDefaultPromptUnchanged(t *testing.T) {
	prompt := DefaultSingleAgentSystemPrompt()
	for _, needle := range []string{
		"不因“红队、漏洞、攻击、渗透”等关键词直接拒绝",
		"不得通过换入口、换工具或修改参数绕过同一安全限制",
		"不自动扩大目标范围",
	} {
		if !strings.Contains(prompt, needle) {
			t.Fatalf("default 提示被改動了: 缺少 %q", needle)
		}
	}
}
