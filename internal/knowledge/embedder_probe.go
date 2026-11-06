package knowledge

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

const probeSnippetLimit = 512

// newProbeRequest 組出與 eino embedder 相同的請求：POST {base}/embeddings。
func newProbeRequest(endpoint, apiKey, model string) (*http.Request, error) {
	body, err := json.Marshal(map[string]any{
		"model": model,
		"input": "ping",
	})
	if err != nil {
		return nil, fmt.Errorf("組請求失敗: %w", err)
	}
	req, err := http.NewRequest(http.MethodPost, endpoint, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("建立請求失敗: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)
	return req, nil
}

// readSnippet 讀取錯誤回應本文並截斷，避免把整個 HTML 錯誤頁噴到終端機。
func readSnippet(resp *http.Response) string {
	raw, err := io.ReadAll(io.LimitReader(resp.Body, probeSnippetLimit))
	if err != nil {
		return "(無法讀取回應本文)"
	}
	return string(bytes.TrimSpace(raw))
}

// parseProbeResponse 從 OpenAI 相容的 embeddings 回應中取出維度與模型名。
func parseProbeResponse(resp *http.Response) (dim int, model string, err error) {
	raw, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if err != nil {
		return 0, "", fmt.Errorf("讀取回應失敗: %w", err)
	}
	var parsed struct {
		Model string `json:"model"`
		Data  []struct {
			Embedding []float64 `json:"embedding"`
		} `json:"data"`
	}
	if err := json.Unmarshal(raw, &parsed); err != nil {
		return 0, "", fmt.Errorf("回應不是合法的 OpenAI embeddings 格式（HTTP 200 但內容不是 JSON 向量）: %w", err)
	}
	if len(parsed.Data) == 0 {
		return 0, parsed.Model, fmt.Errorf("HTTP 200 但 data 為空，該端點可能不是真正的 embedding 服務")
	}
	return len(parsed.Data[0].Embedding), parsed.Model, nil
}
