package handler

import (
	"reflect"
	"strings"
	"testing"

	"jysecai/internal/config"
)

func TestRedactMCPArgsMasksSecretFlags(t *testing.T) {
	cases := []struct {
		name string
		in   []string
		want []string
	}{
		{
			name: "separate value after a secret flag",
			in:   []string{"--api-key", "sk-live-1234567890", "--verbose"},
			want: []string{"--api-key", "***", "--verbose"},
		},
		{
			name: "inline equals form",
			in:   []string{"--api-key=sk-live-1234567890", "--model", "gpt-4o"},
			want: []string{"--api-key=***", "--model", "gpt-4o"},
		},
		{
			name: "password and token flags",
			in:   []string{"-p", "hunter2hunter2", "--token", "abcdef123456", "--auth", "xyz789012345"},
			want: []string{"-p", "***", "--token", "***", "--auth", "***"},
		},
		{
			name: "case insensitive flag matching",
			in:   []string{"--API-KEY", "sk-live-1234567890"},
			want: []string{"--API-KEY", "***"},
		},
		{
			name: "positional secret without a flag",
			in:   []string{"run", "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123"},
			want: []string{"run", "***"},
		},
		{
			name: "ordinary arguments are untouched",
			in:   []string{"--host", "127.0.0.1", "--port", "8737", "--verbose"},
			want: []string{"--host", "127.0.0.1", "--port", "8737", "--verbose"},
		},
		{
			name: "long alphabetic arg is not a token",
			in:   []string{"--verylongdescriptiveflagname"},
			want: []string{"--verylongdescriptiveflagname"},
		},
		{
			name: "nil stays nil",
			in:   nil,
			want: nil,
		},
		{
			name: "empty stays empty",
			in:   []string{},
			want: []string{},
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := redactMCPArgs(tc.in); !reflect.DeepEqual(got, tc.want) {
				t.Errorf("redactMCPArgs(%q) = %q, want %q", tc.in, got, tc.want)
			}
		})
	}
}

// TestRedactMCPArgsRemovesEverySecret walks the input and asserts that none of
// the planted secrets survive anywhere in the output, which is stronger than
// checking the expected shape.
func TestRedactMCPArgsRemovesEverySecret(t *testing.T) {
	secrets := []string{
		"sk-live-1234567890",
		"hunter2hunter2",
		"ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123",
	}
	in := []string{
		"--api-key", secrets[0],
		"-p", secrets[1],
		"positional", secrets[2],
		"--host", "127.0.0.1",
	}
	got := strings.Join(redactMCPArgs(in), " ")
	for _, secret := range secrets {
		if strings.Contains(got, secret) {
			t.Errorf("secret %q survived redaction: %s", secret, got)
		}
	}
	if !strings.Contains(got, "127.0.0.1") {
		t.Errorf("non-secret arg was dropped: %s", got)
	}
}

func TestRedactMCPURLStripsPassword(t *testing.T) {
	cases := map[string]string{
		"https://user:pass@api.example.com/mcp":   "https://user@api.example.com/mcp",
		"https://user:p%40ss@api.example.com/mcp": "https://user@api.example.com/mcp",
		"https://api.example.com/mcp":             "https://api.example.com/mcp",
		"https://:onlypass@api.example.com/mcp":   "https://api.example.com/mcp",
		"http://127.0.0.1:8737/mcp":               "http://127.0.0.1:8737/mcp",
		"":                                        "",
		"not a url at all":                        "not a url at all",
	}
	for in, want := range cases {
		if got := redactMCPURL(in); got != want {
			t.Errorf("redactMCPURL(%q) = %q, want %q", in, got, want)
		}
	}
	if got := redactMCPURL("https://user:sup3rs3cret@api.example.com/mcp"); strings.Contains(got, "sup3rs3cret") {
		t.Errorf("password survived redaction: %q", got)
	}
}

// TestMergeExternalMCPSecretsRestoresPositionalArgs is the round-trip guard. The
// client posts back the redacted list; without positional restore, saving the
// form would write the literal "***" into config.yaml and break the MCP server.
func TestMergeExternalMCPSecretsRestoresPositionalArgs(t *testing.T) {
	current := config.ExternalMCPServerConfig{
		Args: []string{"--api-key", "sk-live-1234567890", "--model", "gpt-4o"},
	}
	incoming := config.ExternalMCPServerConfig{
		Args: []string{"--api-key", "***", "--model", "gpt-4o"},
	}
	got := mergeExternalMCPSecrets(incoming, current)
	if !reflect.DeepEqual(got.Args, current.Args) {
		t.Errorf("Args = %q, want %q", got.Args, current.Args)
	}
	for _, arg := range got.Args {
		if arg == "***" {
			t.Fatal("mask placeholder was written back into the stored args")
		}
	}
}

// TestMergeExternalMCPSecretsKeepsEditedArgs ensures the merge is not a
// blanket overwrite — the operator must still be able to change a flag.
func TestMergeExternalMCPSecretsKeepsEditedArgs(t *testing.T) {
	current := config.ExternalMCPServerConfig{
		Args: []string{"--api-key", "sk-old", "--model", "gpt-4o"},
	}
	incoming := config.ExternalMCPServerConfig{
		Args: []string{"--api-key", "***", "--model", "gpt-4o-mini"},
	}
	got := mergeExternalMCPSecrets(incoming, current)
	if got.Args[1] != "sk-old" {
		t.Errorf("masked secret not restored: %q", got.Args[1])
	}
	if got.Args[3] != "gpt-4o-mini" {
		t.Errorf("genuine edit was discarded: %q", got.Args[3])
	}
}

// TestMergeExternalMCPSecretsRestoresURLUserinfo covers the http/sse endpoint
// case, where redaction strips only the password.
func TestMergeExternalMCPSecretsRestoresURLUserinfo(t *testing.T) {
	current := config.ExternalMCPServerConfig{
		URL: "https://svc:sup3rs3cret@api.example.com/mcp",
	}
	incoming := config.ExternalMCPServerConfig{
		URL: "https://svc@api.example.com/mcp",
	}
	got := mergeExternalMCPSecrets(incoming, current)
	if got.URL != current.URL {
		t.Errorf("URL = %q, want %q", got.URL, current.URL)
	}

	// An edit to the rest of the URL must survive alongside the restore.
	edited := mergeExternalMCPSecrets(
		config.ExternalMCPServerConfig{URL: "https://svc@other.example.com/mcp"}, current)
	if !strings.Contains(edited.URL, "other.example.com") || !strings.Contains(edited.URL, "sup3rs3cret") {
		t.Errorf("URL edit lost or credential not restored: %q", edited.URL)
	}
}

// TestMergeExternalMCPSecretsRestoresEnvAndHeaders covers the map-based fields.
func TestMergeExternalMCPSecretsRestoresEnvAndHeaders(t *testing.T) {
	current := config.ExternalMCPServerConfig{
		Env:     map[string]string{"API_KEY": "sk-old", "LOG_LEVEL": "info"},
		Headers: map[string]string{"Authorization": "Bearer tok-old"},
	}
	incoming := config.ExternalMCPServerConfig{
		Env:     map[string]string{"API_KEY": "***", "LOG_LEVEL": "debug"},
		Headers: map[string]string{"Authorization": "***"},
	}
	got := mergeExternalMCPSecrets(incoming, current)
	if got.Env["API_KEY"] != "sk-old" {
		t.Errorf("Env API_KEY = %q, want sk-old", got.Env["API_KEY"])
	}
	if got.Env["LOG_LEVEL"] != "debug" {
		t.Errorf("Env LOG_LEVEL = %q, want debug", got.Env["LOG_LEVEL"])
	}
	if got.Headers["Authorization"] != "Bearer tok-old" {
		t.Errorf("Headers Authorization = %q, want restored", got.Headers["Authorization"])
	}
}

// TestExternalMCPConfigForResponseRedacts drives the function the API actually
// serializes, so the assertions match the bytes on the wire.
func TestExternalMCPConfigForResponseRedacts(t *testing.T) {
	const secret = "sk-live-mcp-1234567890"
	cfg := config.ExternalMCPServerConfig{
		URL:     "https://svc:urlpass@api.example.com/mcp",
		Args:    []string{"--api-key", secret, "--host", "127.0.0.1"},
		Env:     map[string]string{"API_KEY": secret},
		Headers: map[string]string{"Authorization": "Bearer " + secret},
	}
	copyCfg := externalMCPConfigForResponse(nil, cfg)
	joined := strings.Join(copyCfg.Args, " ") + " " + copyCfg.URL + " " +
		copyCfg.Env["API_KEY"] + " " + copyCfg.Headers["Authorization"]
	if strings.Contains(joined, secret) || strings.Contains(joined, "urlpass") {
		t.Errorf("secret survived redaction: %q", joined)
	}
	if !strings.Contains(joined, "127.0.0.1") {
		t.Errorf("non-secret field was dropped: %q", joined)
	}
	// The source config must be untouched.
	if cfg.Args[1] != secret || !strings.Contains(cfg.URL, "urlpass") {
		t.Fatal("redaction mutated the source config")
	}
}
