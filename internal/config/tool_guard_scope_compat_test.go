package config

import (
	"os"
	"path/filepath"
	"testing"

	"jysecai/internal/toolguard"
)

// 舊格式相容性驗證：生產環境的 config.yaml 是既有版本寫出的，
// 沒有 tool_guard 區塊，或有區塊但沒有 scope 欄位。
// 這些情況都必須維持原本行為，且不得阻止服務啟動。

func TestLegacyConfigWithoutToolGuard(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "config.yaml")
	// 完全沒有 tool_guard 區塊（最舊格式）
	legacy := "server:\n  host: 127.0.0.1\n  port: 8080\nlog:\n  level: info\n"
	if err := os.WriteFile(path, []byte(legacy), 0o600); err != nil {
		t.Fatal(err)
	}
	cfg, err := Load(path)
	if err != nil {
		t.Fatalf("legacy config without tool_guard must load: %v", err)
	}
	effective := cfg.EffectiveToolGuard()
	if !effective.Enabled || len(effective.Rules) == 0 {
		t.Fatalf("default protection must be applied, got %+v", effective)
	}
	policy, err := toolguard.Compile(effective)
	if err != nil {
		t.Fatalf("default policy must compile: %v", err)
	}
	// 舊設定載入後，政府目標仍必須被阻擋（行為不變）
	if policy.Check("http_request", map[string]interface{}{"target": "https://portal.agency.gov.example"}) == nil {
		t.Fatal("legacy config must keep blocking government targets")
	}
	// Scope 必須是 nil，才能確保不會被寫回 config.yaml
	if effective.Scope != nil {
		t.Fatalf("legacy config must yield nil scope, got %+v", effective.Scope)
	}
}

func TestLegacyConfigWithToolGuardButNoScope(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "config.yaml")
	// 有 tool_guard 區塊，但只有 enabled + rules（這是加入 scope 之前的格式）
	legacy := `server:
  host: 127.0.0.1
  port: 8080
tool_guard:
  enabled: true
  rules:
    - id: government-domains
      name: 政府网站保护
      enabled: true
      pattern: '(?i)gov'
      message: '禁止攻击 {match}'
`
	if err := os.WriteFile(path, []byte(legacy), 0o600); err != nil {
		t.Fatal(err)
	}
	cfg, err := Load(path)
	if err != nil {
		t.Fatalf("legacy tool_guard without scope must load: %v", err)
	}
	effective := cfg.EffectiveToolGuard()
	if effective.Scope != nil {
		t.Fatalf("scope must be nil when absent from YAML, got %+v", effective.Scope)
	}
	policy, err := toolguard.Compile(effective)
	if err != nil {
		t.Fatal(err)
	}
	if policy.Check("http_request", map[string]interface{}{"target": "https://status.city.gov.example"}) == nil {
		t.Fatal("government target must remain blocked under legacy config")
	}
}

func TestConfigWithScopeRoundTrip(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "config.yaml")
	withScope := `server:
  host: 127.0.0.1
  port: 8080
tool_guard:
  enabled: true
  rules:
    - id: government-domains
      name: 政府网站保护
      enabled: true
      pattern: '(?i)gov'
      message: '禁止攻击 {match}'
  scope:
    domains:
      - portal.agency.gov.example
    domain_suffixes:
      - .department.gov.example
    cidrs:
      - 192.0.2.10/32
`
	if err := os.WriteFile(path, []byte(withScope), 0o600); err != nil {
		t.Fatal(err)
	}
	cfg, err := Load(path)
	if err != nil {
		t.Fatalf("config with scope must load: %v", err)
	}
	scope := cfg.EffectiveToolGuard().Scope
	if scope == nil {
		t.Fatal("scope must be present when declared in YAML")
	}
	if len(scope.Domains) != 1 || scope.Domains[0] != "portal.agency.gov.example" {
		t.Fatalf("unexpected domains: %+v", scope.Domains)
	}
	policy, err := toolguard.Compile(cfg.EffectiveToolGuard())
	if err != nil {
		t.Fatal(err)
	}
	// 範圍內放行
	if m := policy.Check("http_request", map[string]interface{}{"target": "https://portal.agency.gov.example:4000/config"}); m != nil {
		t.Fatalf("scoped target must be allowed, got %+v", m)
	}
	// 範圍外仍阻擋
	if m := policy.Check("http_request", map[string]interface{}{"target": "https://status.city.gov.example"}); m == nil {
		t.Fatal("out-of-scope government target must remain blocked")
	}
}
