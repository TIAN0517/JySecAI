package knowledge

import (
	"fmt"
	"net/http"
	"strings"
	"time"

	"jysecai/internal/config"
)

// ResolvedEmbedding 是知識庫實際會拿來呼叫的 embedding 設定，附帶每個欄位的來源。
//
// 為什麼需要這個型別：歷史上 knowledge.embedding 留空時會直接繼承 OpenAI 聊天設定
// （app.go 兩處初始化各寫了一份）。這在「聊天端點同時提供 /v1/embeddings」時沒問題，
// 但聊天模型（MiniMax-M3.1-Flash-Preview、Jy Gateway…）本身不提供 embeddings 路由，
// 繼承之後就會對 /v1/embeddings 拿到 404，而錯誤訊息完全不會指出設定是從哪繼承來的。
// 這裡把來源記錄下來，讓啟動日誌與 cmd/knowledge-doctor 都能指認真正的成因。
type ResolvedEmbedding struct {
	Provider string
	Model    string
	BaseURL  string
	APIKey   string

	// 這些欄位標示該值是否由 OpenAI 聊天設定繼承而來。
	ModelInherited    bool
	BaseURLInherited  bool
	APIKeyInherited   bool
	PlaceholderAPIKey bool
}

// ResolveEmbeddingConfig 解析知識庫實際使用的 embedding 設定，不修改傳入的設定。
//
// openAI 為 nil 時等同於沒有聊天設定可繼承。
func ResolveEmbeddingConfig(k *config.KnowledgeConfig, openAI *config.OpenAIConfig) ResolvedEmbedding {
	res := ResolvedEmbedding{}
	if k == nil {
		return res
	}

	res.Provider = strings.TrimSpace(k.Embedding.Provider)
	res.Model = strings.TrimSpace(k.Embedding.Model)
	res.BaseURL = strings.TrimSpace(k.Embedding.BaseURL)
	res.APIKey = strings.TrimSpace(k.Embedding.APIKey)

	if openAI != nil {
		if res.APIKey == "" {
			res.APIKey = strings.TrimSpace(openAI.APIKey)
			res.APIKeyInherited = true
		}
		if res.BaseURL == "" {
			res.BaseURL = strings.TrimSpace(openAI.BaseURL)
			res.BaseURLInherited = true
		}
	}

	if res.Model == "" {
		res.Model = "text-embedding-3-small"
		res.ModelInherited = true
	}
	res.BaseURL = strings.TrimSuffix(res.BaseURL, "/")
	if res.BaseURL == "" {
		res.BaseURL = "https://api.openai.com/v1"
	}

	// sk-xxxxxxx 之類的範例佔位符。這種值不會被 API 拒絕得很乾淨，
	// 通常表現為 401 或更難懂的回應，先在本地就標出來。
	res.PlaceholderAPIKey = isPlaceholderKey(res.APIKey)
	return res
}

// isPlaceholderKey 判斷看起來是範例檔留下的假金鑰。
func isPlaceholderKey(key string) bool {
	if key == "" {
		return false
	}
	lower := strings.ToLower(key)
	if !strings.HasPrefix(lower, "sk-") {
		return false
	}
	body := lower[3:]
	if body == "" {
		return false
	}
	// 純 x、全 0、全同一字元都視為佔位符
	if strings.Trim(body, "x") == "" {
		return true
	}
	if strings.Trim(body, "0") == "" {
		return true
	}
	// 同一字元連續 5 個以上（例如 sk-aaaaaaaa）也是佔位符
	if len(body) >= 5 {
		same := true
		for i := 1; i < len(body); i++ {
			if body[i] != body[0] {
				same = false
				break
			}
		}
		return same
	}
	return false
}

// Diagnostics 回傳這份設定在啟動前就已知的所有問題。
// 這些是「不需要打網路就能確定」的問題。
func (r ResolvedEmbedding) Diagnostics() []string {
	var out []string

	if r.APIKey == "" {
		out = append(out, "沒有 embedding API key：knowledge.embedding.api_key 留空，且 OpenAI 聊天設定也沒有 api_key")
	} else if r.PlaceholderAPIKey {
		out = append(out, fmt.Sprintf(
			"embedding API key 仍是範例檔的佔位符（長度 %d）：knowledge.embedding.api_key 必須換成真的 key",
			len(r.APIKey)))
	}

	if r.BaseURL == "" {
		out = append(out, "沒有 embedding base_url")
	}

	// 最容易踩到的坑：聊天端點被拿來當 embedding 端點。
	if r.BaseURLInherited && r.APIKeyInherited {
		out = append(out, fmt.Sprintf(
			"embedding 的 base_url 與 api_key 都從 OpenAI 聊天設定繼承而來（%s）。"+
				"聊天端點通常沒有 /embeddings 路由，除非該端點另外提供 embedding 模型，否則一定 404。"+
				"請在 knowledge.embedding 明確指定 base_url / model / api_key。",
			r.BaseURL))
	}
	return out
}

// EmbeddingProbeResult 是對 embedding 端點實測的結果。
type EmbeddingProbeResult struct {
	OK       bool
	Endpoint string
	Dim      int
	Model    string
	// StatusCode 與 Body 僅在失敗時有意義，Body 已截斷。
	StatusCode int
	Body       string
	Err        error
}

// ProbeEmbedding 對實際會使用的端點送一次真實請求。
//
// 這是刻意不重用 eino embedder 的：診斷工具需要拿到 HTTP 狀態碼與回應本文，
// 才能分辨 404（沒有這條路由）與 401（金鑰錯）這兩種完全不同的成因。
func ProbeEmbedding(client *http.Client, r ResolvedEmbedding, timeout time.Duration) EmbeddingProbeResult {
	res := EmbeddingProbeResult{Endpoint: strings.TrimSuffix(r.BaseURL, "/") + "/embeddings", Model: r.Model}
	if r.APIKey == "" {
		res.Err = fmt.Errorf("沒有 API key，未送出請求")
		return res
	}
	if client == nil {
		client = &http.Client{}
	}
	if timeout <= 0 {
		timeout = 30 * time.Second
	}

	req, err := newProbeRequest(res.Endpoint, r.APIKey, r.Model)
	if err != nil {
		res.Err = err
		return res
	}
	resp, err := client.Do(req)
	if err != nil {
		res.Err = err
		return res
	}
	defer resp.Body.Close()
	res.StatusCode = resp.StatusCode

	if resp.StatusCode != http.StatusOK {
		res.Body = readSnippet(resp)
		return res
	}

	dim, model, err := parseProbeResponse(resp)
	if err != nil {
		res.Err = err
		return res
	}
	res.OK = true
	res.Dim = dim
	if model != "" {
		res.Model = model
	}
	return res
}

// AutoIndexAllowed reports whether startup indexing should run. A dead embedding
// origin must not be retried across every knowledge item on each process start.
func AutoIndexAllowed(probe EmbeddingProbeResult) (bool, string) {
	if probe.OK {
		return true, ""
	}
	if probe.StatusCode != 0 {
		return false, fmt.Sprintf("embedding HTTP %d", probe.StatusCode)
	}
	if probe.Err != nil {
		return false, probe.Err.Error()
	}
	if probe.Body != "" {
		return false, probe.Body
	}
	return false, "embedding probe failed"
}
