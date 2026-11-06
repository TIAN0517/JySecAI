package handler

import (
	"strings"
	"testing"
)

func TestXSSTokenHintDoesNotExposeToken(t *testing.T) {
	const token = "sensitive-xss-collector-token"
	hint := xssTokenHint(token)
	if hint == "" || strings.Contains(hint, token) || len(hint) >= len(token) {
		t.Fatalf("unsafe token hint: %q", hint)
	}
	if hint != xssTokenHint(token) {
		t.Fatal("token hint should be stable for correlation")
	}
}
