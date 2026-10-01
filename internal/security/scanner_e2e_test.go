package security

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"jysecai/internal/config"
	"jysecai/internal/failure"
	"jysecai/internal/observability"
	"jysecai/internal/toolschema"
	"jysecai/internal/tooltarget"
	"go.uber.org/zap"
)

// TestScannerRetryStormE2E 模擬 Agent 自動循環的 retry-storm 場景：
//
//   PHASE A：Agent 連續呼叫 nuclei 但從未提供 target。
//   預期：每次都收到 STOP_FOR_INPUT；tool_execution_total 為 0；
//         tool_search_total ≤ 1。
//
//   PHASE B：模擬使用者補上一個授權目標（例如 127.0.0.1）。
//   預期：新的邏輯呼叫；fake nuclei 程序執行 1 次；
//         結果包含 fake 二進位的輸出。
//
// 不實際掃描任何外部目標；fake nuclei 是 TempDir 下的 shell script。
func TestScannerRetryStormE2E(t *testing.T) {
	policy := tooltarget.NewConfigAuthorizedTargetPolicy()
	policy.Replace(tooltarget.Config{Entries: []tooltarget.Entry{
		{Tool: "nuclei", Host: "127.0.0.1", Note: "loopback fixture"},
	}})

	// 安裝 fake nuclei：echo 一個穩定字串 + exit 0。
	binDir := t.TempDir()
	fakeBin := filepath.Join(binDir, "nuclei")
	script := "#!/bin/sh\necho \"fake-nuclei-ran target=$1\"\nexit 0\n"
	if err := os.WriteFile(fakeBin, []byte(script), 0o755); err != nil {
		t.Fatalf("write fake nuclei: %v", err)
	}

	cfg := &config.SecurityConfig{
		Tools: []config.ToolConfig{
			{
				Name: "nuclei", Command: fakeBin, Enabled: true,
				Parameters: []config.ParameterConfig{
					{Name: "target", Type: "string", Required: true, Flag: "-u", Format: "flag"},
				},
			},
		},
	}

	e := NewExecutor(cfg, nil, zap.NewNop())
	registry := toolschema.NewRegistry()
	registry.Set(toolschema.NewSnapshot(cfg.Tools))
	metrics := observability.New()
	e.SetScannerHooks(registry, policy, metrics, ExecutionModeAgent)

	// PHASE A: agent 不斷要求 nuclei 但沒提供 target。
	// 預期所有呼叫都被 STOP_FOR_INPUT 阻擋；nuclei 程序執行次數 = 0。
	const attempts = 20
	for i := 0; i < attempts; i++ {
		res, err := e.ExecuteTool(context.Background(), "nuclei", map[string]interface{}{})
		if err != nil {
			t.Fatalf("phase A attempt %d: %v", i, err)
		}
		if res == nil || len(res.Content) == 0 {
			t.Fatalf("phase A attempt %d: empty result", i)
		}
		text := res.Content[0].Text
		var env scannerErrorEnvelope
		if err := json.Unmarshal([]byte(text), &env); err != nil {
			t.Fatalf("phase A attempt %d: parse envelope: %v (raw=%s)", i, err, text)
		}
		if env.Code != string(failure.CodeMissingRequiredArgument) {
			t.Fatalf("phase A attempt %d: code=%q want MISSING_REQUIRED_ARGUMENT", i, env.Code)
		}
		if !env.RequiresUserInput {
			t.Fatalf("phase A attempt %d: requires_user_input must be true", i)
		}
	}
	if got := metrics.Count(observability.CounterToolStopForInputTotal, "nuclei", string(failure.CodeMissingRequiredArgument)); got != int64(attempts) {
		t.Fatalf("phase A: stop_for_input want %d, got %d", attempts, got)
	}
	if got := metrics.Count(observability.CounterToolExecutionTotal, "nuclei", ""); got != 0 {
		t.Fatalf("phase A: nuclei execution must stay 0, got %d", got)
	}

	// PHASE B: 模擬使用者補上授權的 127.0.0.1 目標。
	// 預期 fake nuclei 程序執行一次，輸出含 "fake-nuclei-ran"。
	res, err := e.ExecuteTool(context.Background(), "nuclei", map[string]interface{}{
		"target": "http://127.0.0.1:8080",
	})
	if err != nil {
		t.Fatalf("phase B: %v", err)
	}
	if res == nil || len(res.Content) == 0 {
		t.Fatalf("phase B: empty result")
	}
	text := res.Content[0].Text
	if !strings.Contains(text, "fake-nuclei-ran") {
		t.Fatalf("phase B: expected fake nuclei output, got %s", text)
	}
	// 第二次檢查：execution 計數必須為 1（PHASE A 全 STOP_FOR_INPUT）。
	if got := metrics.Count(observability.CounterToolExecutionTotal, "nuclei", ""); got != 1 {
		t.Fatalf("phase B: nuclei execution want 1, got %d", got)
	}
	if got := metrics.Count(observability.CounterToolStopForInputTotal, "nuclei", string(failure.CodeMissingRequiredArgument)); got != int64(attempts) {
		// STOP_FOR_INPUT 計數必須維持 attempts（phase B 不再增加）。
		t.Fatalf("phase B: stop_for_input should stay %d, got %d", attempts, got)
	}
}

// TestStdioModeAllowsAdditionalArgs 對應 stdio / Manual 操作員路徑的
// 既有行為：additional_args 仍受 Manual 模式相容，不會被視為 POLICY_DENIED。
// 這確保「操作員手工下指令」不會被新版管線意外擋下。
func TestStdioModeAllowsAdditionalArgs(t *testing.T) {
	policy := tooltarget.NewConfigAuthorizedTargetPolicy()
	policy.Replace(tooltarget.Config{Entries: []tooltarget.Entry{
		{Tool: "nuclei", Host: "127.0.0.1"},
	}})

	binDir := t.TempDir()
	fakeBin := filepath.Join(binDir, "nuclei")
	if err := os.WriteFile(fakeBin, []byte("#!/bin/sh\nexit 0\n"), 0o755); err != nil {
		t.Fatalf("write fake nuclei: %v", err)
	}

	cfg := &config.SecurityConfig{
		Tools: []config.ToolConfig{
			{
				Name: "nuclei", Command: fakeBin, Enabled: true,
				Parameters: []config.ParameterConfig{
					{Name: "target", Type: "string", Required: true, Flag: "-u", Format: "flag"},
				},
			},
		},
	}

	e := NewExecutor(cfg, nil, zap.NewNop())
	registry := toolschema.NewRegistry()
	registry.Set(toolschema.NewSnapshot(cfg.Tools))
	metrics := observability.New()
	e.SetScannerHooks(registry, policy, metrics, ExecutionModeManual)

	res, err := e.ExecuteTool(context.Background(), "nuclei", map[string]interface{}{
		"target":          "http://127.0.0.1",
		"additional_args": "-stats",
	})
	if err != nil {
		t.Fatalf("stdio: %v", err)
	}
	if res != nil && len(res.Content) > 0 {
		text := res.Content[0].Text
		if strings.Contains(text, "POLICY_DENIED") {
			t.Fatalf("stdio/manual must allow additional_args, got %s", text)
		}
	}
}