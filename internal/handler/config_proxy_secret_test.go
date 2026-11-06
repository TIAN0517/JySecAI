package handler

import (
	"net/url"
	"testing"

	"jysecai/internal/config"
)

// TestRestoreProxyPoolCredentialsRecoversMaskedUserinfo 迴歸測試：
// 設定頁把遮蔽過的代理 URL 原樣送回來時，userinfo 必須被還原。
//
// 遮蔽後的 URL 是 socks5://%2A%2A%2A...@host:port。若不還原，任何一次無關的
// 設定存檔都會把真實的 SOCKS5 帳密洗成 "********"，代理池直接失效，而且
// saveConfig 會把遮蔽值寫回 config.yaml，真實密碼不可復原。
func TestRestoreProxyPoolCredentialsRecoversMaskedUserinfo(t *testing.T) {
	current := []config.SOCKS5ProxyConfig{
		{URL: "socks5://realuser:realsecret@proxy.example:1080"},
	}
	incoming := []config.SOCKS5ProxyConfig{
		{URL: "socks5://%2A%2A%2A%2A%2A%2A%2A%2A@proxy.example:1080"},
	}

	got := restoreProxyPoolCredentials(incoming, current)
	if len(got) != 1 {
		t.Fatalf("len(got) = %d, want 1", len(got))
	}
	parsed, err := url.Parse(got[0].URL)
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if parsed.User == nil {
		t.Fatalf("userinfo 沒有還原: %q", got[0].URL)
	}
	if user := parsed.User.Username(); user != "realuser" {
		t.Fatalf("username = %q, want realuser", user)
	}
	password, _ := parsed.User.Password()
	if password != "realsecret" {
		t.Fatalf("password = %q, want realsecret", password)
	}
}

// TestRestoreProxyPoolCredentialsKeepsOperatorEditedPassword 使用者真的改過密碼時
// 不能被還原成舊值 —— 否則改不動代理。
func TestRestoreProxyPoolCredentialsKeepsOperatorEditedPassword(t *testing.T) {
	current := []config.SOCKS5ProxyConfig{
		{URL: "socks5://realuser:realsecret@proxy.example:1080"},
	}
	incoming := []config.SOCKS5ProxyConfig{
		{URL: "socks5://realuser:newly-typed@proxy.example:1080"},
	}

	got := restoreProxyPoolCredentials(incoming, current)
	parsed, err := url.Parse(got[0].URL)
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	password, _ := parsed.User.Password()
	if password != "newly-typed" {
		t.Fatalf("password = %q, want newly-typed（使用者輸入的新值必須保留）", password)
	}
}

// TestResolveTestAPIKeyDoesNotLeakKeyToUnmatchedBaseURL 回歸測試：
// base_url 跟任何已儲存通道對不上時，不得回退到預設通道或 openai.api_key。
//
// 舊行為會把平台的生產 LLM 金鑰送到呼叫端指定的第三方端點 —— 那把金鑰是
// maskProviderSecrets 刻意藏起來的。
func TestResolveTestAPIKeyDoesNotLeakKeyToUnmatchedBaseURL(t *testing.T) {
	h := &ConfigHandler{
		config: &config.Config{
			OpenAI: config.OpenAIConfig{APIKey: "sk-top-level-secret", BaseURL: "https://api.openai.com/v1"},
			AI: config.AIConfig{
				DefaultChannel: "primary",
				Channels: map[string]config.AIChannelConfig{
					"primary": {APIKey: "sk-default-channel-secret", BaseURL: "https://api.openai.com/v1", Model: "gpt-4o"},
				},
			},
		},
	}

	got := h.resolveTestAPIKey("********", "https://third-party.example/v1", "gpt-4o")
	if got != "" {
		t.Fatalf("resolveTestAPIKey = %q, want \"\"（base_url 不符時不得還原任何金鑰）", got)
	}

	// base_url 相符時仍然要能還原 —— 本機訂閱橋的測試連線靠這條路徑。
	matched := h.resolveTestAPIKey("********", "https://api.openai.com/v1", "gpt-4o")
	if matched != "sk-default-channel-secret" {
		t.Fatalf("resolveTestAPIKey = %q, want sk-default-channel-secret", matched)
	}
}
