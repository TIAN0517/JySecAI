package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"jysecai/internal/config"

	"github.com/gin-gonic/gin"
)

const testMCPServiceToken = "Bearer s3cr3t-mcp-service-credential"

// TestMaskProviderSecretsDoesNotMutateLiveConfig is the load-bearing test. If
// masking reached through a shared map or pointer into h.config, every stored
// API key would be replaced by the literal "********" the moment an operator
// opened the settings page.
func TestMaskProviderSecretsDoesNotMutateLiveConfig(t *testing.T) {
	live := &config.Config{
		MCP:    config.MCPConfig{AuthHeaderValue: testMCPServiceToken},
		OpenAI: config.OpenAIConfig{APIKey: "sk-live-openai", BaseURL: "https://api.openai.com/v1"},
		Vision: config.VisionConfig{APIKey: "sk-live-vision"},
		FOFA:   config.FofaConfig{APIKey: "fofa-key"},
		AI: config.AIConfig{Channels: map[string]config.AIChannelConfig{
			"primary": {APIKey: "ai-channel-key", Model: "gpt-4o"},
		}},
		ZoomEye:   config.SpaceSearchConfig{APIKey: "zoomeye-key"},
		Quake:     config.SpaceSearchConfig{APIKey: "quake-key"},
		Shodan:    config.SpaceSearchConfig{APIKey: "shodan-key"},
		Knowledge: config.KnowledgeConfig{Embedding: config.EmbeddingConfig{APIKey: "embed-key"}},
	}

	publicCfg := *live
	publicCfg.AI.Channels = make(map[string]config.AIChannelConfig, len(live.AI.Channels))
	for k, v := range live.AI.Channels {
		publicCfg.AI.Channels[k] = v
	}
	maskProviderSecrets(&publicCfg)

	// The public copy must not reveal any secret.
	if publicCfg.MCP.AuthHeaderValue != maskedConfigSecret {
		t.Errorf("MCP.AuthHeaderValue = %q, want masked", publicCfg.MCP.AuthHeaderValue)
	}
	for name, got := range map[string]string{
		"OpenAI":    publicCfg.OpenAI.APIKey,
		"Vision":    publicCfg.Vision.APIKey,
		"FOFA":      publicCfg.FOFA.APIKey,
		"ZoomEye":   publicCfg.ZoomEye.APIKey,
		"Quake":     publicCfg.Quake.APIKey,
		"Shodan":    publicCfg.Shodan.APIKey,
		"Embedding": publicCfg.Knowledge.Embedding.APIKey,
		"AIChannel": publicCfg.AI.Channels["primary"].APIKey,
	} {
		if got != maskedConfigSecret {
			t.Errorf("%s = %q, want masked", name, got)
		}
	}

	// The live config must be completely untouched.
	if live.MCP.AuthHeaderValue != testMCPServiceToken {
		t.Errorf("live MCP.AuthHeaderValue was mutated to %q", live.MCP.AuthHeaderValue)
	}
	if live.OpenAI.APIKey != "sk-live-openai" ||
		live.Vision.APIKey != "sk-live-vision" ||
		live.FOFA.APIKey != "fofa-key" ||
		live.ZoomEye.APIKey != "zoomeye-key" ||
		live.Quake.APIKey != "quake-key" ||
		live.Shodan.APIKey != "shodan-key" ||
		live.Knowledge.Embedding.APIKey != "embed-key" ||
		live.AI.Channels["primary"].APIKey != "ai-channel-key" {
		t.Fatalf("maskProviderSecrets mutated the live config: %+v", live)
	}
	// Non-secret fields stay readable so the settings form still populates.
	if publicCfg.AI.Channels["primary"].Model != "gpt-4o" {
		t.Errorf("model = %q, want gpt-4o", publicCfg.AI.Channels["primary"].Model)
	}
	if publicCfg.OpenAI.BaseURL != "https://api.openai.com/v1" {
		t.Errorf("base_url was masked: %q", publicCfg.OpenAI.BaseURL)
	}
}

// TestMergeProviderSecretsIntoRestoresMaskedValues is the round-trip half. The
// UI posts back what it got from GetConfig, so every masked field arriving at
// UpdateConfig must be swapped for the stored value rather than persisted.
func TestMergeProviderSecretsIntoRestoresMaskedValues(t *testing.T) {
	current := &config.Config{
		MCP:    config.MCPConfig{AuthHeaderValue: testMCPServiceToken},
		OpenAI: config.OpenAIConfig{APIKey: "sk-live-openai"},
		Vision: config.VisionConfig{APIKey: "sk-live-vision"},
		FOFA:   config.FofaConfig{APIKey: "fofa-key"},
		AI: config.AIConfig{Channels: map[string]config.AIChannelConfig{
			"primary": {APIKey: "ai-channel-key"},
		}},
		ZoomEye:   config.SpaceSearchConfig{APIKey: "zoomeye-key"},
		Quake:     config.SpaceSearchConfig{APIKey: "quake-key"},
		Shodan:    config.SpaceSearchConfig{APIKey: "shodan-key"},
		Knowledge: config.KnowledgeConfig{Embedding: config.EmbeddingConfig{APIKey: "embed-key"}},
	}

	// Simulate the round-trip: every secret comes back as the mask placeholder.
	req := UpdateConfigRequest{
		MCP:       &config.MCPConfig{AuthHeaderValue: maskedConfigSecret},
		OpenAI:    &config.OpenAIConfig{APIKey: maskedConfigSecret},
		Vision:    &config.VisionConfig{APIKey: maskedConfigSecret},
		FOFA:      &config.FofaConfig{APIKey: maskedConfigSecret},
		ZoomEye:   &config.SpaceSearchConfig{APIKey: maskedConfigSecret},
		Quake:     &config.SpaceSearchConfig{APIKey: maskedConfigSecret},
		Shodan:    &config.SpaceSearchConfig{APIKey: maskedConfigSecret},
		AI:        &config.AIConfig{Channels: map[string]config.AIChannelConfig{"primary": {APIKey: maskedConfigSecret}}},
		Knowledge: &config.KnowledgeConfig{Embedding: config.EmbeddingConfig{APIKey: maskedConfigSecret}},
	}
	mergeProviderSecretsInto(&req, current)

	if req.MCP.AuthHeaderValue != testMCPServiceToken {
		t.Errorf("MCP.AuthHeaderValue = %q, want the stored token", req.MCP.AuthHeaderValue)
	}
	if req.OpenAI.APIKey != "sk-live-openai" ||
		req.Vision.APIKey != "sk-live-vision" ||
		req.FOFA.APIKey != "fofa-key" ||
		req.ZoomEye.APIKey != "zoomeye-key" ||
		req.Quake.APIKey != "quake-key" ||
		req.Shodan.APIKey != "shodan-key" ||
		req.Knowledge.Embedding.APIKey != "embed-key" ||
		req.AI.Channels["primary"].APIKey != "ai-channel-key" {
		t.Fatalf("masked values were not restored: %+v", req)
	}
}

// TestMergeProviderSecretsIntoKeepsGenuineNewKeys ensures the merge is not a
// blanket overwrite: an operator rotating a key must actually be able to.
func TestMergeProviderSecretsIntoKeepsGenuineNewKeys(t *testing.T) {
	current := &config.Config{
		MCP:    config.MCPConfig{AuthHeaderValue: testMCPServiceToken},
		OpenAI: config.OpenAIConfig{APIKey: "sk-old"},
		AI: config.AIConfig{Channels: map[string]config.AIChannelConfig{
			"primary": {APIKey: "old-channel-key"},
		}},
	}
	req := UpdateConfigRequest{
		MCP:    &config.MCPConfig{AuthHeaderValue: "Bearer rotated-token"},
		OpenAI: &config.OpenAIConfig{APIKey: "sk-new"},
		AI: &config.AIConfig{Channels: map[string]config.AIChannelConfig{
			"primary": {APIKey: "new-channel-key"},
		}},
	}
	mergeProviderSecretsInto(&req, current)

	if req.MCP.AuthHeaderValue != "Bearer rotated-token" {
		t.Errorf("genuine new MCP token was discarded: %q", req.MCP.AuthHeaderValue)
	}
	if req.OpenAI.APIKey != "sk-new" {
		t.Errorf("genuine new key was discarded: %q", req.OpenAI.APIKey)
	}
	if req.AI.Channels["primary"].APIKey != "new-channel-key" {
		t.Errorf("genuine new channel key was discarded: %q", req.AI.Channels["primary"].APIKey)
	}
}

func TestResolveTestAPIKeyRestoresMaskedChannelKey(t *testing.T) {
	h := &ConfigHandler{config: &config.Config{
		AI: config.AIConfig{
			DefaultChannel: "gpt-daybreak",
			Channels: map[string]config.AIChannelConfig{
				"gpt-daybreak": {
					APIKey:  "jysec-codex-bridge",
					BaseURL: "http://127.0.0.1:18787/v1",
					Model:   "gpt-daybreak-blue-latest",
				},
				"other": {
					APIKey:  "other-key",
					BaseURL: "https://example.com/v1",
					Model:   "other",
				},
			},
		},
		OpenAI: config.OpenAIConfig{APIKey: "sk-fallback"},
	}}

	got := h.resolveTestAPIKey(maskedConfigSecret, "http://127.0.0.1:18787/v1", "gpt-daybreak-blue-latest")
	if got != "jysec-codex-bridge" {
		t.Fatalf("masked probe key = %q, want stored channel key", got)
	}
	got = h.resolveTestAPIKey("typed-fresh-key", "http://127.0.0.1:18787/v1", "gpt-daybreak-blue-latest")
	if got != "typed-fresh-key" {
		t.Fatalf("explicit key was overwritten: %q", got)
	}
	got = h.resolveTestAPIKey(maskedConfigSecret, "http://127.0.0.1:18787/v1", "")
	if got != "jysec-codex-bridge" {
		t.Fatalf("list-models base-only resolve = %q, want stored channel key", got)
	}
}

// TestGetConfigResponseCarriesNoSecrets drives the real handler and greps the
// serialized body, which is what actually reaches the browser.
func TestGetConfigResponseCarriesNoSecrets(t *testing.T) {
	gin.SetMode(gin.TestMode)

	const mcpToken = testMCPServiceToken
	const openaiKey = "sk-live-openai-abcdef"
	const fofaKey = "fofa-live-key"
	const embedKey = "embed-live-key"
	const zoomEyeKey = "zoomeye-live-key"

	cfg := &config.Config{
		MCP:     config.MCPConfig{AuthHeaderValue: mcpToken},
		OpenAI:  config.OpenAIConfig{APIKey: openaiKey, BaseURL: "https://api.openai.com/v1"},
		FOFA:    config.FofaConfig{APIKey: fofaKey},
		ZoomEye: config.SpaceSearchConfig{APIKey: zoomEyeKey},
		AI: config.AIConfig{Channels: map[string]config.AIChannelConfig{
			"primary": {APIKey: "ai-live-channel-key"},
		}},
		Knowledge: config.KnowledgeConfig{Embedding: config.EmbeddingConfig{APIKey: embedKey}},
	}

	h := &ConfigHandler{config: cfg}
	router := gin.New()
	router.GET("/api/config", h.GetConfig)

	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/api/config", nil))

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, body = %s", rec.Code, rec.Body.String())
	}

	for name, secret := range map[string]string{
		"mcp_auth_header": mcpToken,
		"openai_api_key":  openaiKey,
		"fofa_api_key":    fofaKey,
		"zoomeye_api_key": zoomEyeKey,
		"embedding_key":   embedKey,
		"ai_channel_key":  "ai-live-channel-key",
	} {
		if bytes.Contains(rec.Body.Bytes(), []byte(secret)) {
			t.Errorf("%s leaked in GET /api/config response", name)
		}
	}

	// The response must still be valid JSON carrying the masked placeholder,
	// otherwise the settings page cannot round-trip the value back.
	var parsed GetConfigResponse
	if err := json.Unmarshal(rec.Body.Bytes(), &parsed); err != nil {
		t.Fatalf("response is not valid JSON: %v", err)
	}
	if parsed.MCP.AuthHeaderValue != maskedConfigSecret {
		t.Errorf("parsed MCP.AuthHeaderValue = %q, want masked", parsed.MCP.AuthHeaderValue)
	}
	if parsed.OpenAI.APIKey != maskedConfigSecret {
		t.Errorf("parsed OpenAI.APIKey = %q, want masked", parsed.OpenAI.APIKey)
	}
	if parsed.OpenAI.BaseURL != "https://api.openai.com/v1" {
		t.Errorf("base_url should stay readable, got %q", parsed.OpenAI.BaseURL)
	}
	if cc := rec.Header().Get("Cache-Control"); cc != "no-store" {
		t.Errorf("Cache-Control = %q, want no-store", cc)
	}
}
