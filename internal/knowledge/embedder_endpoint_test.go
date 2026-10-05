package knowledge

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"go.uber.org/zap"
	"jysecai/internal/config"
)

func TestEmbeddingBaseURLUsesAPIPrefixAndRetriesAfterConfigurationRepair(t *testing.T) {
	var paths []string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		paths = append(paths, r.URL.Path)
		if r.URL.Path != "/compatible/v1/embeddings" {
			w.Header().Set("Content-Type", "text/html")
			w.WriteHeader(http.StatusNotFound)
			_, _ = w.Write([]byte("<html><title>Test Console</title>404</html>"))
			return
		}
		if r.Method != http.MethodPost {
			t.Errorf("method=%s", r.Method)
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{
			"object": "list", "model": "test-embedding",
			"data": []any{map[string]any{"object": "embedding", "index": 0, "embedding": []float64{0.1, 0.2}}},
		})
	}))
	defer server.Close()
	cfg := &config.KnowledgeConfig{Embedding: config.EmbeddingConfig{BaseURL: server.URL, Model: "test-embedding", APIKey: "synthetic-test-only"}}
	bad, err := NewEmbedder(context.Background(), cfg, nil, zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	if _, err := bad.EmbedText(context.Background(), "non-sensitive test"); err == nil {
		t.Fatal("console endpoint unexpectedly worked")
	}
	cfg.Embedding.BaseURL = server.URL + "/compatible/v1/"
	good, err := NewEmbedder(context.Background(), cfg, nil, zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	vector, err := good.EmbedText(context.Background(), "non-sensitive test")
	if err != nil || len(vector) != 2 {
		t.Fatalf("correct endpoint: vector=%v err=%v", vector, err)
	}
	if len(paths) != 2 || paths[0] != "/embeddings" || paths[1] != "/compatible/v1/embeddings" {
		t.Fatalf("requests=%v", paths)
	}
}
