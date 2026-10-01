package config

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"gopkg.in/yaml.v3"
)

func TestSensitiveConfigProtectionRoundTrip(t *testing.T) {
	t.Setenv("JYSECAI_CONFIG_KEY", "")
	t.Setenv("JYSECAI_CREDENTIAL_KEY", "")
	path := filepath.Join(t.TempDir(), "config.yaml")
	robots := RobotsConfig{}
	robots.Wecom.Token = "wecom-token"
	robots.Telegram.BotToken = "telegram-token"
	external := ExternalMCPConfig{Servers: map[string]ExternalMCPServerConfig{
		"demo": {Headers: map[string]string{"Authorization": "Bearer secret"}, Env: map[string]string{"API_KEY": "secret-key"}},
	}}
	protectedRobots, protectedExternal, err := ProtectSensitiveConfig(path, robots, external)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(protectedRobots.Wecom.Token, protectedConfigPrefix) || !strings.HasPrefix(protectedExternal.Servers["demo"].Env["API_KEY"], protectedConfigPrefix) {
		t.Fatalf("secrets were not protected: robots=%#v external=%#v", protectedRobots, protectedExternal)
	}
	cfg := Config{Robots: protectedRobots, ExternalMCP: protectedExternal}
	if err := unprotectSensitiveConfig(path, &cfg); err != nil {
		t.Fatal(err)
	}
	if cfg.Robots.Wecom.Token != robots.Wecom.Token || cfg.ExternalMCP.Servers["demo"].Headers["Authorization"] != "Bearer secret" {
		t.Fatalf("round trip mismatch: %#v", cfg)
	}
}

func TestConfigLoadDecryptsProtectedSecrets(t *testing.T) {
	t.Setenv("JYSECAI_CONFIG_KEY", "")
	t.Setenv("JYSECAI_CREDENTIAL_KEY", "")
	path := filepath.Join(t.TempDir(), "config.yaml")
	robots := RobotsConfig{}
	robots.Telegram.BotToken = "telegram-token"
	protected, _, err := ProtectSensitiveConfig(path, robots, ExternalMCPConfig{})
	if err != nil {
		t.Fatal(err)
	}
	raw, err := yaml.Marshal(Config{Robots: protected})
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, raw, 0o600); err != nil {
		t.Fatal(err)
	}
	cfg, err := Load(path)
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Robots.Telegram.BotToken != "telegram-token" {
		t.Fatalf("decrypted token = %q", cfg.Robots.Telegram.BotToken)
	}
}
