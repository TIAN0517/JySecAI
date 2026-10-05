package knowledge

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"jysecai/internal/config"
)

func TestResolveEmbeddingConfigKeepsExplicitValues(t *testing.T) {
	kb := &config.KnowledgeConfig{Embedding: config.EmbeddingConfig{
		Provider: "openai",
		Model:    "text-embedding-v4",
		BaseURL:  "https://dashscope.aliyuncs.com/compatible-mode/v1/",
		APIKey:   "sk-real-looking-key-0123456789",
	}}
	openAI := &config.OpenAIConfig{APIKey: "sk-chat-key", BaseURL: "https://chat.example/v1"}

	got := ResolveEmbeddingConfig(kb, openAI)

	if got.Model != "text-embedding-v4" {
		t.Errorf("model = %q, want text-embedding-v4", got.Model)
	}
	// 結尾斜線必須被去掉，否則組出 ".../v1//embeddings"
	if got.BaseURL != "https://dashscope.aliyuncs.com/compatible-mode/v1" {
		t.Errorf("baseURL = %q, want trailing slash trimmed", got.BaseURL)
	}
	if got.BaseURLInherited || got.APIKeyInherited {
		t.Errorf("explicit config must not be marked inherited: %+v", got)
	}
	if got.PlaceholderAPIKey {
		t.Error("a real-looking key must not be flagged as placeholder")
	}
	if diags := got.Diagnostics(); len(diags) != 0 {
		t.Errorf("expected no diagnostics, got %v", diags)
	}
}

func TestResolveEmbeddingConfigInheritsAndFlagsChatEndpoint(t *testing.T) {
	kb := &config.KnowledgeConfig{}
	openAI := &config.OpenAIConfig{APIKey: "sk-chat-key", BaseURL: "https://api.minimaxi.com/anthropic"}

	got := ResolveEmbeddingConfig(kb, openAI)

	if !got.BaseURLInherited || !got.APIKeyInherited {
		t.Fatalf("expected both fields marked inherited, got %+v", got)
	}
	if got.BaseURL != "https://api.minimaxi.com/anthropic" {
		t.Errorf("baseURL = %q, want inherited value", got.BaseURL)
	}
	// 空 model 應回退到預設，且標記為 defaulted 而非 inherited
	if got.Model != "text-embedding-3-small" || !got.ModelInherited {
		t.Errorf("model = %q (defaulted=%v), want text-embedding-3-small defaulted", got.Model, got.ModelInherited)
	}

	// 這是最容易踩的坑：聊天端點沒有 /embeddings 路由
	diags := got.Diagnostics()
	if len(diags) == 0 {
		t.Fatal("expected a diagnostic when embedding config is fully inherited from chat settings")
	}
	if !strings.Contains(diags[0], "/embeddings") {
		t.Errorf("diagnostic should mention the missing route, got: %s", diags[0])
	}
}

func TestPlaceholderKeyDetection(t *testing.T) {
	cases := map[string]bool{
		"sk-xxxxxxx":          true,
		"sk-xxxxxxxx":         true,
		"sk-000000":           true,
		"sk-aaaaaaaa":         true,
		"sk-real-key-1234567": false,
		"":                    false,
		"not-a-sk-key":        false,
	}
	for key, want := range cases {
		if got := isPlaceholderKey(key); got != want {
			t.Errorf("isPlaceholderKey(%q) = %v, want %v", key, got, want)
		}
	}
}

func TestProbeEmbeddingReportsOKAndDimension(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/embeddings" {
			t.Errorf("path = %q, want /v1/embeddings", r.URL.Path)
		}
		if got := r.Header.Get("Authorization"); got != "Bearer sk-test" {
			t.Errorf("authorization = %q", got)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{
			"object": "list",
			"model":  "text-embedding-v4",
			"data":   []any{map[string]any{"embedding": []float64{0.1, 0.2, 0.3}}},
		})
	}))
	defer srv.Close()

	got := ProbeEmbedding(nil, ResolvedEmbedding{BaseURL: srv.URL + "/v1", APIKey: "sk-test", Model: "text-embedding-v4"}, 0)
	if !got.OK {
		t.Fatalf("probe failed: %+v", got)
	}
	if got.Dim != 3 {
		t.Errorf("dim = %d, want 3", got.Dim)
	}
	if got.Model != "text-embedding-v4" {
		t.Errorf("model = %q", got.Model)
	}
}

func TestProbeEmbeddingDistinguishes404From401(t *testing.T) {
	// 404：端點存在但沒有 /embeddings 路由（聊天端點的典型症狀）
	notFound := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
		_, _ = w.Write([]byte("<html>404 Not Found</html>"))
	}))
	defer notFound.Close()

	got := ProbeEmbedding(nil, ResolvedEmbedding{BaseURL: notFound.URL, APIKey: "sk-test", Model: "m"}, 0)
	if got.OK {
		t.Fatal("404 must not be reported as OK")
	}
	if got.StatusCode != http.StatusNotFound {
		t.Errorf("status = %d, want 404", got.StatusCode)
	}
	report := &DoctorReport{Resolved: ResolvedEmbedding{BaseURL: notFound.URL}}
	applyProbeFinding(report, got)
	if !containsSubstring(report.Findings, "沒有 /embeddings 路由") {
		t.Errorf("404 should produce a route-missing finding, got %+v", report.Findings)
	}

	// 401：金鑰錯，成因完全不同，不能跟 404 混為一談
	unauthorized := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusUnauthorized)
		_, _ = w.Write([]byte(`{"error":{"message":"invalid api key"}}`))
	}))
	defer unauthorized.Close()

	got2 := ProbeEmbedding(nil, ResolvedEmbedding{BaseURL: unauthorized.URL, APIKey: "sk-bad", Model: "m"}, 0)
	report2 := &DoctorReport{Resolved: ResolvedEmbedding{BaseURL: unauthorized.URL}}
	applyProbeFinding(report2, got2)
	if !containsSubstring(report2.Findings, "金鑰被拒絕") {
		t.Errorf("401 should produce a key-rejected finding, got %+v", report2.Findings)
	}
}

func TestProbeEmbeddingRejects200WithNonEmbeddingBody(t *testing.T) {
	// 有些網關的 catch-all 路由會回 200 加一段 HTML，那不是 embedding 服務
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		_, _ = w.Write([]byte("<html>console</html>"))
	}))
	defer srv.Close()

	got := ProbeEmbedding(nil, ResolvedEmbedding{BaseURL: srv.URL, APIKey: "sk-test", Model: "m"}, 0)
	if got.OK {
		t.Fatal("HTML 200 must not be reported as a working embedding endpoint")
	}
	if got.Err == nil {
		t.Fatal("expected an error describing the malformed response")
	}
}

func TestRunDoctorEndToEnd(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewEncoder(w).Encode(map[string]any{
			"model": "test-embed",
			"data":  []any{map[string]any{"embedding": []float64{0.5, 0.5}}},
		})
	}))
	defer srv.Close()

	dir := t.TempDir()
	path := filepath.Join(dir, "config.yaml")
	body := "version: v1.7.1\n" +
		"knowledge:\n" +
		"  enabled: true\n" +
		"  base_path: knowledge_base\n" +
		"  embedding:\n" +
		"    provider: openai\n" +
		"    model: test-embed\n" +
		"    base_url: " + srv.URL + "\n" +
		"    api_key: sk-test-key-0123456789\n"
	if err := os.WriteFile(path, []byte(body), 0o600); err != nil {
		t.Fatal(err)
	}

	report, err := RunDoctor(DoctorOptions{ConfigPath: path, SkipProbe: true})
	if err != nil {
		t.Fatalf("RunDoctor: %v", err)
	}
	if !report.Healthy() {
		t.Errorf("expected healthy report, findings: %+v", report.Findings)
	}
	if !report.Enabled {
		t.Error("expected knowledge.enabled = true")
	}
	// JSON 輸出絕不能含完整金鑰
	raw := string(report.JSON())
	if strings.Contains(raw, "sk-test-key-0123456789") {
		t.Error("JSON output leaked the full API key")
	}
}

func TestRunDoctorRequiresConfigPath(t *testing.T) {
	if _, err := RunDoctor(DoctorOptions{}); err == nil {
		t.Fatal("expected an error when --config is missing")
	}
}

func containsSubstring(findings []Finding, sub string) bool {
	for _, f := range findings {
		if strings.Contains(f.Message, sub) {
			return true
		}
	}
	return false
}
