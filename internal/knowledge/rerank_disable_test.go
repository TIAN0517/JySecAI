package knowledge

import (
	"testing"

	"jysecai/internal/config"

	"go.uber.org/zap"
)

func TestRerankDisabledRecognizesExplicitOffValues(t *testing.T) {
	for _, v := range []string{"none", "off", "disabled", "false", "None", "OFF", " disabled "} {
		rc := config.RerankConfig{Provider: v}
		if !rc.RerankDisabled() {
			t.Errorf("provider=%q should be treated as disabled", v)
		}
	}
	for _, v := range []string{"", "cohere", "dashscope", "local"} {
		rc := config.RerankConfig{Provider: v}
		if rc.RerankDisabled() {
			t.Errorf("provider=%q should NOT be treated as disabled", v)
		}
	}
}

// 這是換成本機 embedding 端點時會踩到的坑：provider 留空會被推斷成 cohere，
// 導致每次檢索都去呼叫本機不存在的 /v1/rerank。設成 none 必須真的關掉。
func TestProviderEffectiveDoesNotSilentlyAssumeCohereWhenDisabled(t *testing.T) {
	rc := config.RerankConfig{Provider: config.RerankDisabledProvider}
	if got := rc.ProviderEffective("http://127.0.0.1:11434/v1"); got != config.RerankDisabledProvider {
		t.Errorf("ProviderEffective = %q, want %q (must not fall back to cohere)", got, config.RerankDisabledProvider)
	}
	if got := rc.ModelEffective(config.RerankDisabledProvider); got != "rerank-multilingual-v3.0" {
		// ModelEffective 對未知 provider 仍回 cohere 的預設值，但因為 rerank 根本不會被呼叫，
		// 這個值不影響行為。記錄目前行為，避免未來有人誤以為它有意義。
		t.Logf("note: ModelEffective(%q) = %q (unused when rerank is disabled)", config.RerankDisabledProvider, got)
	}
}

func TestNewHTTPRerankerReturnsNilWhenDisabled(t *testing.T) {
	openAI := &config.OpenAIConfig{APIKey: "sk-chat", BaseURL: "https://chat.example/v1"}

	got, err := NewHTTPReranker(&config.RerankConfig{Provider: "none"}, openAI, zap.NewNop())
	if err != nil {
		t.Fatalf("disabled rerank must not error, got %v", err)
	}
	if got != nil {
		t.Fatalf("disabled rerank must return nil, got %+v", got)
	}
	// 關閉時不該因為缺少 api_key/base_url 而報錯
	if _, err := NewHTTPReranker(&config.RerankConfig{Provider: "off"}, nil, zap.NewNop()); err != nil {
		t.Errorf("disabled rerank with nil openAI config must not error, got %v", err)
	}
}

func TestNewHTTPRerankerStillValidatesWhenEnabled(t *testing.T) {
	// 開啟時的既有行為不能被這次改動影響：缺 api_key 仍然要報錯
	_, err := NewHTTPReranker(&config.RerankConfig{Provider: "cohere"}, nil, zap.NewNop())
	if err == nil {
		t.Fatal("expected an error when rerank is enabled but no api_key is available")
	}
}

// typed nil 陷阱：把 (*HTTPReranker)(nil) 塞進 interface 會讓 != nil 成立，
// pipeline 就會每次查詢都呼叫它。這裡模擬呼叫端的判斷，確保回傳值能安全使用。
func TestDisabledRerankerIsSafeForInterfaceAssignment(t *testing.T) {
	rr, err := NewHTTPReranker(&config.RerankConfig{Provider: "none"}, nil, zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	var iface DocumentReranker
	if rr != nil { // 這是 wire_retriever.go 的判斷方式
		iface = rr
	}
	if iface != nil {
		t.Error("assigning a disabled reranker must leave the interface nil, otherwise the pipeline will call it")
	}
}
