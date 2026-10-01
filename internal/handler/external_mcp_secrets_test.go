package handler

import (
	"testing"

	"jysecai/internal/config"
)

func TestExternalMCPSecretsAlwaysMaskedAndPreserved(t *testing.T) {
	original := config.ExternalMCPServerConfig{
		Env:     map[string]string{"API_KEY": "secret"},
		Headers: map[string]string{"Authorization": "Bearer secret"},
	}
	masked := externalMCPConfigForResponse(nil, original)
	if masked.Env["API_KEY"] != "***" || masked.Headers["Authorization"] != "***" {
		t.Fatalf("secrets were exposed: %#v", masked)
	}
	merged := mergeExternalMCPSecrets(masked, original)
	if merged.Env["API_KEY"] != "secret" || merged.Headers["Authorization"] != "Bearer secret" {
		t.Fatalf("masked values were not preserved: %#v", merged)
	}
}
