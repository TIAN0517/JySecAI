package config

import (
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"

	"gopkg.in/yaml.v3"
)

func TestEnsureLocalConfigCreatesFromExample(t *testing.T) {
	dir := t.TempDir()
	examplePath := filepath.Join(dir, "config.example.yaml")
	configPath := filepath.Join(dir, "config.yaml")

	example := []byte(`auth:
  session_duration_hours: 12
server:
  host: 127.0.0.1
  port: 8080
`)
	if err := os.WriteFile(examplePath, example, 0644); err != nil {
		t.Fatalf("write example: %v", err)
	}

	result, err := EnsureLocalConfig(configPath)
	if err != nil {
		t.Fatalf("EnsureLocalConfig: %v", err)
	}
	if !result.Created {
		t.Fatal("Created = false, want true")
	}
	if result.ExamplePath != examplePath {
		t.Fatalf("ExamplePath = %q, want %q", result.ExamplePath, examplePath)
	}

	cfg, err := Load(configPath)
	if err != nil {
		t.Fatalf("Load generated config: %v", err)
	}
	if cfg.Auth.SessionDurationHours != 12 {
		t.Fatalf("SessionDurationHours = %d, want 12", cfg.Auth.SessionDurationHours)
	}
	assertPrivateConfigMode(t, configPath)

	// Existing configurations can predate the private-permission policy.
	// Startup must tighten them without changing their contents.
	before, err := os.ReadFile(configPath)
	if err != nil {
		t.Fatalf("read generated config: %v", err)
	}
	if err := os.Chmod(configPath, 0644); err != nil {
		t.Fatalf("chmod generated config: %v", err)
	}

	second, err := EnsureLocalConfig(configPath)
	if err != nil {
		t.Fatalf("EnsureLocalConfig existing: %v", err)
	}
	if second.Created {
		t.Fatal("Created = true for existing config, want false")
	}
	assertPrivateConfigMode(t, configPath)
	after, err := os.ReadFile(configPath)
	if err != nil {
		t.Fatalf("read tightened config: %v", err)
	}
	if string(after) != string(before) {
		t.Fatal("EnsureLocalConfig modified existing config contents")
	}
}

func TestEnsureMCPAuthRewritesConfigWithPrivatePermissions(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "config.yaml")
	initial := []byte("mcp:\n  enabled: true\n  allow_global_access: true\n  auth_header: X-MCP-Token\n  auth_header_value: \"\"\n")
	if err := os.WriteFile(path, initial, 0644); err != nil {
		t.Fatalf("write config: %v", err)
	}
	if err := os.Chmod(path, 0644); err != nil {
		t.Fatalf("chmod config: %v", err)
	}

	cfg := &Config{MCP: MCPConfig{
		Enabled:           true,
		AllowGlobalAccess: true,
		AuthHeader:        "X-MCP-Token",
	}}
	if err := EnsureMCPAuth(path, cfg); err != nil {
		t.Fatalf("EnsureMCPAuth: %v", err)
	}
	if strings.TrimSpace(cfg.MCP.AuthHeaderValue) == "" {
		t.Fatal("EnsureMCPAuth did not generate a service credential")
	}
	assertPrivateConfigMode(t, path)
	written, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read rewritten config: %v", err)
	}
	if !strings.Contains(string(written), cfg.MCP.AuthHeaderValue) {
		t.Fatal("generated service credential was not persisted")
	}
}

func TestEnsureXSSSecretGeneratesAndPersistsToken(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "config.yaml")
	initial := []byte("xss:\n  enabled: true\n  bind_host: 127.0.0.1\n  bind_port: 8877\n  cooldown_seconds: 60\n")
	if err := os.WriteFile(path, initial, 0644); err != nil {
		t.Fatalf("write config: %v", err)
	}
	if err := os.Chmod(path, 0644); err != nil {
		t.Fatalf("chmod config: %v", err)
	}

	enabled := true
	cfg := &Config{XSS: XSSConfig{Enabled: &enabled, BindHost: "127.0.0.1", BindPort: 8877, CooldownSeconds: 60}}
	if err := EnsureXSSSecret(path, cfg); err != nil {
		t.Fatalf("EnsureXSSSecret: %v", err)
	}
	if strings.TrimSpace(cfg.XSS.Token) == "" {
		t.Fatal("EnsureXSSSecret did not generate a token")
	}
	assertPrivateConfigMode(t, path)
	written, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read rewritten config: %v", err)
	}
	if !strings.Contains(string(written), cfg.XSS.Token) {
		t.Fatal("generated XSS token was not persisted")
	}

	// 已存在 token 时不应覆盖。
	reload, err := Load(path)
	if err != nil {
		t.Fatalf("reload: %v", err)
	}
	if !reload.XSS.EnabledEffective() || reload.XSS.Token != cfg.XSS.Token {
		t.Fatalf("reload XSS state mismatch: enabled=%v token=%q", reload.XSS.EnabledEffective(), reload.XSS.Token)
	}
}

func TestEnsureXSSSecretDisabledNoWrite(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "config.yaml")
	initial := []byte("xss:\n  enabled: false\n")
	if err := os.WriteFile(path, initial, 0644); err != nil {
		t.Fatalf("write config: %v", err)
	}
	disabled := false
	cfg := &Config{XSS: XSSConfig{Enabled: &disabled}}
	if err := EnsureXSSSecret(path, cfg); err != nil {
		t.Fatalf("EnsureXSSSecret disabled: %v", err)
	}
	written, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read config: %v", err)
	}
	if strings.Contains(string(written), "token") {
		t.Fatal("EnsureXSSSecret wrote a token while disabled")
	}
}

func assertPrivateConfigMode(t *testing.T, path string) {
	t.Helper()
	info, err := os.Stat(path)
	if err != nil {
		t.Fatalf("stat %s: %v", path, err)
	}
	if runtime.GOOS == "windows" {
		// Windows has no POSIX mode bits: os.Chmod only toggles the read-only
		// attribute and Mode().Perm() always reports 0666/0444. The 0600
		// contract is enforced on POSIX platforms where it is representable.
		return
	}
	if got := info.Mode().Perm(); got != 0600 {
		t.Fatalf("%s permissions = %04o, want 0600", path, got)
	}
}

func TestLoadIgnoresLegacyAuthPasswordField(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "config.yaml")
	initial := strings.Join([]string{
		"auth:",
		`  password: "legacy-password"`,
		"  session_duration_hours: 12",
		"server:",
		"  host: 127.0.0.1",
		"  port: 8080",
		"",
	}, "\n")
	if err := os.WriteFile(path, []byte(initial), 0644); err != nil {
		t.Fatalf("write config: %v", err)
	}

	cfg, err := Load(path)
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if cfg.Auth.SessionDurationHours != 12 {
		t.Fatalf("SessionDurationHours = %d, want 12", cfg.Auth.SessionDurationHours)
	}
}

func TestHitlAuditModelEffectiveFallsBackToMainConfig(t *testing.T) {
	main := OpenAIConfig{
		Provider: "openai",
		BaseURL:  "https://api.example.com/v1",
		APIKey:   "main-key",
		Model:    "large-model",
	}

	got := (HitlConfig{
		AuditModel: OpenAIConfig{Model: "small-reviewer"},
	}).AuditModelEffective(main)

	if got.Provider != main.Provider || got.BaseURL != main.BaseURL || got.APIKey != main.APIKey {
		t.Fatalf("expected provider/base_url/api_key to inherit main config, got %+v", got)
	}
	if got.Model != "small-reviewer" {
		t.Fatalf("expected audit model override, got %q", got.Model)
	}
}

func TestHitlDefaultConfigEffectiveValues(t *testing.T) {
	if got := (HitlConfig{}).EffectiveDefaultMode(); got != "off" {
		t.Fatalf("empty default mode = %q, want off", got)
	}
	if got := (HitlConfig{DefaultMode: "review-edit"}).EffectiveDefaultMode(); got != "off" {
		t.Fatalf("unknown default mode = %q, want off", got)
	}
	if got := (HitlConfig{DefaultMode: "review_edit"}).EffectiveDefaultMode(); got != "review_edit" {
		t.Fatalf("review_edit default mode = %q, want review_edit", got)
	}
	if got := (HitlConfig{}).EffectiveDefaultTimeoutSeconds(); got != 300 {
		t.Fatalf("empty default timeout = %d, want 300", got)
	}
	zero := 0
	if got := (HitlConfig{DefaultTimeoutSeconds: &zero}).EffectiveDefaultTimeoutSeconds(); got != 0 {
		t.Fatalf("zero default timeout = %d, want 0", got)
	}
	neg := -1
	if got := (HitlConfig{DefaultTimeoutSeconds: &neg}).EffectiveDefaultTimeoutSeconds(); got != 0 {
		t.Fatalf("negative default timeout = %d, want 0", got)
	}
}

func TestLoadUsesAIDefaultChannelAsRuntimeOpenAI(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "config.yaml")
	initial := strings.Join([]string{
		"ai:",
		"  default_channel: deepseek",
		"  channels:",
		"    qwen:",
		"      name: Qwen",
		"      provider: openai_compatible",
		"      base_url: https://dashscope.example/v1",
		"      api_key: qwen-key",
		"      model: qwen-max",
		"    deepseek:",
		"      name: DeepSeek",
		"      provider: openai_compatible",
		"      base_url: https://deepseek.example/v1",
		"      api_key: deepseek-key",
		"      model: deepseek-chat",
		"      max_total_tokens: 64000",
		"server:",
		"  host: 127.0.0.1",
		"  port: 8080",
		"",
	}, "\n")
	if err := os.WriteFile(path, []byte(initial), 0644); err != nil {
		t.Fatalf("write config: %v", err)
	}

	cfg, err := Load(path)
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if cfg.OpenAI.Model != "deepseek-chat" || cfg.OpenAI.APIKey != "deepseek-key" || cfg.OpenAI.MaxTotalTokens != 64000 {
		t.Fatalf("runtime OpenAI config did not follow ai.default_channel: %+v", cfg.OpenAI)
	}
	oa, id, ok := cfg.ResolveAIChannel("qwen")
	if !ok || id != "qwen" || oa.Model != "qwen-max" || oa.APIKey != "qwen-key" {
		t.Fatalf("ResolveAIChannel(qwen) = (%+v, %q, %v)", oa, id, ok)
	}
}

func TestNormalizeAIProviderProfilesForOfficialDeepSeekEndpoint(t *testing.T) {
	cfg := &Config{
		OpenAI: OpenAIConfig{
			BaseURL: "https://api.deepseek.com/v1",
			Model:   "deepseek-chat",
			Reasoning: OpenAIReasoningConfig{
				Profile: "openai_compat",
			},
		},
		AI: AIConfig{
			Channels: map[string]AIChannelConfig{
				"official": {
					BaseURL: "api.deepseek.com/v1",
					Model:   "deepseek-chat",
					Reasoning: OpenAIReasoningConfig{
						Profile: "auto",
					},
				},
				"gateway": {
					BaseURL: "https://compatible.example.com/v1",
					Model:   "deepseek-chat",
					Reasoning: OpenAIReasoningConfig{
						Profile: "openai_compat",
					},
				},
			},
		},
	}

	cfg.NormalizeAIProviderProfiles()

	if cfg.OpenAI.Reasoning.Profile != "deepseek" {
		t.Fatalf("openai profile = %q, want deepseek", cfg.OpenAI.Reasoning.Profile)
	}
	if got := cfg.AI.Channels["official"].Reasoning.Profile; got != "deepseek" {
		t.Fatalf("official channel profile = %q, want deepseek", got)
	}
	if got := cfg.AI.Channels["gateway"].Reasoning.Profile; got != "openai_compat" {
		t.Fatalf("gateway profile should be preserved, got %q", got)
	}
}

func TestLoadNormalizesDefaultChannelForOfficialDeepSeekEndpoint(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "config.yaml")
	initial := strings.Join([]string{
		"ai:",
		"  default_channel: deepseek",
		"  channels:",
		"    deepseek:",
		"      name: DeepSeek",
		"      provider: openai_compatible",
		"      base_url: https://api.deepseek.com/v1",
		"      api_key: deepseek-key",
		"      model: deepseek-chat",
		"      reasoning:",
		"        profile: openai_compat",
		"server:",
		"  host: 127.0.0.1",
		"  port: 8080",
		"",
	}, "\n")
	if err := os.WriteFile(path, []byte(initial), 0644); err != nil {
		t.Fatalf("write config: %v", err)
	}

	cfg, err := Load(path)
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if cfg.OpenAI.Reasoning.Profile != "deepseek" {
		t.Fatalf("runtime OpenAI profile = %q, want deepseek", cfg.OpenAI.Reasoning.Profile)
	}
	if got := cfg.AI.Channels["deepseek"].Reasoning.Profile; got != "deepseek" {
		t.Fatalf("channel profile = %q, want deepseek", got)
	}
}

func TestSummarizationUserIntentLedgerRunesEffective(t *testing.T) {
	var zero MultiAgentEinoMiddlewareConfig
	if got := zero.SummarizationUserIntentLedgerMaxRunesEffective(); got != DefaultSummarizationUserIntentLedgerMaxRunes {
		t.Fatalf("default ledger max runes = %d, want %d", got, DefaultSummarizationUserIntentLedgerMaxRunes)
	}
	if got := zero.SummarizationUserIntentLedgerEntryMaxRunesEffective(); got != DefaultSummarizationUserIntentLedgerEntryMaxRunes {
		t.Fatalf("default ledger entry max runes = %d, want %d", got, DefaultSummarizationUserIntentLedgerEntryMaxRunes)
	}

	custom := MultiAgentEinoMiddlewareConfig{
		SummarizationUserIntentLedgerMaxRunes:      12345,
		SummarizationUserIntentLedgerEntryMaxRunes: 2345,
	}
	if got := custom.SummarizationUserIntentLedgerMaxRunesEffective(); got != 12345 {
		t.Fatalf("custom ledger max runes = %d", got)
	}
	if got := custom.SummarizationUserIntentLedgerEntryMaxRunesEffective(); got != 2345 {
		t.Fatalf("custom ledger entry max runes = %d", got)
	}
}

func TestSummarizationOutputReserveTokensEffective(t *testing.T) {
	var zero MultiAgentEinoMiddlewareConfig
	if got := zero.SummarizationOutputReserveTokensEffective(); got != DefaultSummarizationOutputReserveTokens {
		t.Fatalf("default output reserve = %d, want %d", got, DefaultSummarizationOutputReserveTokens)
	}
	custom := MultiAgentEinoMiddlewareConfig{SummarizationOutputReserveTokens: 4096}
	if got := custom.SummarizationOutputReserveTokensEffective(); got != 4096 {
		t.Fatalf("custom output reserve = %d", got)
	}
}

func TestOpenAIOutputLimitValidation(t *testing.T) {
	if got := (OpenAIConfig{}).MaxCompletionTokensEffective(); got != DefaultMaxCompletionTokens {
		t.Fatalf("max completion default=%d", got)
	}
	if err := validateOpenAIOutputLimits(OpenAIConfig{MaxCompletionTokens: -1}); err == nil {
		t.Fatal("negative completion limit must fail")
	}
}

func TestLatestUserMessageRunesEffective(t *testing.T) {
	var zero MultiAgentEinoMiddlewareConfig
	if got := zero.LatestUserMessageMaxRunesEffective(); got != DefaultLatestUserMessageMaxRunes {
		t.Fatalf("default latest user max runes = %d, want %d", got, DefaultLatestUserMessageMaxRunes)
	}
	if got := zero.LatestUserMessageHeadRunesEffective(); got != DefaultLatestUserMessageHeadRunes {
		t.Fatalf("default latest user head runes = %d, want %d", got, DefaultLatestUserMessageHeadRunes)
	}
	if got := zero.LatestUserMessageTailRunesEffective(); got != DefaultLatestUserMessageTailRunes {
		t.Fatalf("default latest user tail runes = %d, want %d", got, DefaultLatestUserMessageTailRunes)
	}

	custom := MultiAgentEinoMiddlewareConfig{
		LatestUserMessageMaxRunes:  100,
		LatestUserMessageHeadRunes: 40,
		LatestUserMessageTailRunes: 60,
	}
	if got := custom.LatestUserMessageMaxRunesEffective(); got != 100 {
		t.Fatalf("custom latest user max runes = %d", got)
	}
	if got := custom.LatestUserMessageHeadRunesEffective(); got != 40 {
		t.Fatalf("custom latest user head runes = %d", got)
	}
	if got := custom.LatestUserMessageTailRunesEffective(); got != 60 {
		t.Fatalf("custom latest user tail runes = %d", got)
	}
}

func TestC2AutoCheckinConfigParseAndEffective(t *testing.T) {
	raw := []byte(`c2:
  enabled: true
  auto_checkin:
    enabled: true
    auto_start_listeners: false
    default_sleep_seconds: 9
    default_jitter_percent: 15
    stale_session_timeout_seconds: 120
    listeners:
      - name: auto-http
        type: http_beacon
        bind_host: 127.0.0.1
        bind_port: 8899
        enabled: true
      - name: auto-ws
        type: websocket
        bind_host: 0.0.0.0
        bind_port: 8900
        enabled: false
`)
	var cfg Config
	if err := yaml.Unmarshal(raw, &cfg); err != nil {
		t.Fatalf("yaml.Unmarshal: %v", err)
	}
	ac := cfg.C2.AutoCheckin
	if ac == nil {
		t.Fatal("C2.AutoCheckin = nil, want parsed config")
	}
	if !ac.EnabledEffective() {
		t.Fatal("auto_checkin should be enabled")
	}
	if ac.AutoStartListenersEffective() {
		t.Fatal("auto_start_listeners should be false")
	}
	if got := ac.DefaultSleepSecondsEffective(); got != 9 {
		t.Fatalf("default sleep = %d, want 9", got)
	}
	if got := ac.DefaultJitterPercentEffective(); got != 15 {
		t.Fatalf("default jitter = %d, want 15", got)
	}
	if got := ac.StaleSessionTimeoutSecondsEffective(); got != 120 {
		t.Fatalf("stale timeout = %d, want 120", got)
	}
	enabled := ac.EnabledAutoListeners()
	if len(enabled) != 1 || enabled[0].Name != "auto-http" {
		t.Fatalf("enabled auto listeners = %+v, want only auto-http", enabled)
	}
	pub := cfg.C2.Public()
	if !pub.Enabled {
		t.Fatal("C2 public enabled = false")
	}
	if pub.AutoCheckin.DefaultSleepSeconds != 9 ||
		pub.AutoCheckin.DefaultJitterPercent != 15 ||
		pub.AutoCheckin.StaleSessionTimeoutSeconds != 120 ||
		pub.AutoCheckin.ListenerCount != 1 {
		t.Fatalf("C2 public auto_checkin = %+v", pub.AutoCheckin)
	}
}

func TestC2AutoCheckinDefaultsWhenAbsent(t *testing.T) {
	// 未写 auto_checkin：视为启用 + 默认参数（与旧 config.yaml 兼容）。
	var cfg Config
	if err := yaml.Unmarshal([]byte("c2:\n  enabled: true\n"), &cfg); err != nil {
		t.Fatalf("yaml.Unmarshal: %v", err)
	}
	var ac *C2AutoCheckinConfig
	if cfg.C2.AutoCheckin != nil {
		ac = cfg.C2.AutoCheckin
	}
	if !ac.EnabledEffective() {
		t.Fatal("auto_checkin absent should default to enabled")
	}
	if !ac.AutoStartListenersEffective() {
		t.Fatal("auto_start_listeners absent should default to true")
	}
	if got := ac.DefaultSleepSecondsEffective(); got != 5 {
		t.Fatalf("default sleep = %d, want 5", got)
	}
	if got := ac.DefaultJitterPercentEffective(); got != 0 {
		t.Fatalf("default jitter = %d, want 0", got)
	}
	if got := ac.StaleSessionTimeoutSecondsEffective(); got != 0 {
		t.Fatalf("stale timeout = %d, want 0 (watchdog default)", got)
	}
	if len(ac.EnabledAutoListeners()) != 0 {
		t.Fatal("no listeners configured, EnabledAutoListeners should be empty")
	}
	if got := cfg.C2.Public().AutoCheckin.ListenerCount; got != 0 {
		t.Fatalf("listener count = %d, want 0", got)
	}
}

func TestC2AutoCheckinEffectiveClamps(t *testing.T) {
	raw := []byte(`c2:
  auto_checkin:
    default_jitter_percent: 500
    default_sleep_seconds: -3
    stale_session_timeout_seconds: -1
`)
	var cfg Config
	if err := yaml.Unmarshal(raw, &cfg); err != nil {
		t.Fatalf("yaml.Unmarshal: %v", err)
	}
	ac := cfg.C2.AutoCheckin
	if ac == nil {
		t.Fatal("C2.AutoCheckin = nil")
	}
	if got := ac.DefaultSleepSecondsEffective(); got != 5 {
		t.Fatalf("default sleep = %d, want fallback 5", got)
	}
	if got := ac.DefaultJitterPercentEffective(); got != 100 {
		t.Fatalf("default jitter = %d, want clamp 100", got)
	}
	if got := ac.StaleSessionTimeoutSecondsEffective(); got != 0 {
		t.Fatalf("stale timeout = %d, want 0 (disable override)", got)
	}
}
