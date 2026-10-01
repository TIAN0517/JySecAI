package mcp

import (
	"crypto/sha256"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"testing"

	"jysecai/internal/config"
)

func TestExternalMCPRemoteHTTPRequiresExplicitCompatibility(t *testing.T) {
	cfg := config.ExternalMCPServerConfig{Type: "http", URL: "http://example.com/mcp"}
	if err := ValidateExternalMCPServerSecurity(cfg); err == nil {
		t.Fatal("remote plaintext HTTP should be rejected")
	}
	cfg.AllowInsecureHTTP = true
	if err := ValidateExternalMCPServerSecurity(cfg); err != nil {
		t.Fatalf("explicit compatibility flag should be accepted: %v", err)
	}
	cfg.AllowInsecureHTTP = false
	cfg.URL = "http://127.0.0.1:8080/mcp"
	if err := ValidateExternalMCPServerSecurity(cfg); err != nil {
		t.Fatalf("loopback HTTP should be accepted: %v", err)
	}
}

func TestExternalMCPRedirectCannotPivotFromRemoteToLoopback(t *testing.T) {
	policy := secureMCPRedirectPolicy(false)
	origin := &http.Request{URL: &url.URL{Scheme: "https", Host: "remote.example"}}
	target := &http.Request{URL: &url.URL{Scheme: "http", Host: "127.0.0.1:8080"}}
	if err := policy(target, []*http.Request{origin}); err == nil {
		t.Fatal("remote server must not redirect MCP client into loopback HTTP")
	}
	localOrigin := &http.Request{URL: &url.URL{Scheme: "http", Host: "localhost:3000"}}
	if err := policy(target, []*http.Request{localOrigin}); err != nil {
		t.Fatalf("local compatibility redirect should remain available: %v", err)
	}
}

func TestExternalMCPEnvironmentDoesNotInheritSecretsByDefault(t *testing.T) {
	t.Setenv("JYSECAI_TEST_SECRET", "must-not-leak")
	env := envMapToSlice(map[string]string{"EXPLICIT_VALUE": "ok"}, false)
	for _, item := range env {
		if item == "JYSECAI_TEST_SECRET=must-not-leak" {
			t.Fatal("parent secret leaked into MCP subprocess")
		}
	}
	env = envMapToSlice(nil, true)
	found := false
	for _, item := range env {
		if item == "JYSECAI_TEST_SECRET=must-not-leak" {
			found = true
		}
	}
	if !found {
		t.Fatal("explicit inherit_parent_env should preserve compatibility")
	}
}

func TestExternalMCPCommandRootAndDigestPin(t *testing.T) {
	executable, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(executable)
	if err != nil {
		t.Fatal(err)
	}
	sum := sha256.Sum256(data)
	cfg := config.ExternalMCPServerConfig{
		Type: "stdio", Command: executable,
		AllowedCommandRoots: []string{filepath.Dir(executable)},
		CommandSHA256:       fmt.Sprintf("%x", sum[:]),
	}
	if _, err := validateExternalMCPCommand(cfg); err != nil {
		t.Fatalf("pinned executable should pass: %v", err)
	}
	cfg.CommandSHA256 = fmt.Sprintf("%064x", 1)
	if _, err := validateExternalMCPCommand(cfg); err == nil {
		t.Fatal("digest mismatch should fail closed")
	}
	cfg.CommandSHA256 = ""
	cfg.AllowedCommandRoots = []string{t.TempDir()}
	if _, err := validateExternalMCPCommand(cfg); err == nil {
		t.Fatal("executable outside allowed roots should be rejected")
	}
}
