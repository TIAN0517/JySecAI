package knowledge

import (
	"fmt"
	"testing"
)

func TestCloudflareOriginTimeoutIsNotRetried(t *testing.T) {
	e := &Embedder{}
	err := fmt.Errorf("status code: 522, connection timeout")
	if e.isRetryableError(err) {
		t.Fatal("origin timeout must not be retried")
	}
	if !e.isRetryableError(fmt.Errorf("status code: 503")) {
		t.Fatal("temporary gateway error should still retry")
	}
}

func TestAutoIndexSkipsDeadOrigin(t *testing.T) {
	if ok, _ := AutoIndexAllowed(EmbeddingProbeResult{StatusCode: 522}); ok {
		t.Fatal("522 should skip automatic indexing")
	}
	if ok, _ := AutoIndexAllowed(EmbeddingProbeResult{OK: true, Dim: 1024}); !ok {
		t.Fatal("successful probe should allow indexing")
	}
}
