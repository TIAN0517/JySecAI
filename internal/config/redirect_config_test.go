package config

import (
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func TestLoadParsesRedirectSection(t *testing.T) {
	dir := t.TempDir()
	configPath := filepath.Join(dir, "config.yaml")
	content := []byte(`server:
  host: 127.0.0.1
  port: 8080
redirect:
  enabled: true
  urls:
    - https://97y.me/tjneJ
    - https://97y.me/tjneK
`)
	if err := os.WriteFile(configPath, content, 0644); err != nil {
		t.Fatalf("write config: %v", err)
	}

	cfg, err := Load(configPath)
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if !cfg.Redirect.Enabled {
		t.Fatal("Redirect.Enabled = false, want true")
	}
	want := []string{"https://97y.me/tjneJ", "https://97y.me/tjneK"}
	if !reflect.DeepEqual(cfg.Redirect.URLs, want) {
		t.Fatalf("Redirect.URLs = %#v, want %#v", cfg.Redirect.URLs, want)
	}
	if !cfg.Redirect.EnabledEffective() {
		t.Fatal("Redirect.EnabledEffective() = false, want true")
	}
}

func TestLoadNormalizesRedirectURLs(t *testing.T) {
	dir := t.TempDir()
	configPath := filepath.Join(dir, "config.yaml")
	content := []byte(`server:
  host: 127.0.0.1
  port: 8080
redirect:
  enabled: false
  urls:
    - "  https://97y.me/tjneJ  "
    - https://97y.me/tjneJ
    - ftp://97y.me/tjneL
    - 97y.me/tjneM
    - ""
`)
	if err := os.WriteFile(configPath, content, 0644); err != nil {
		t.Fatalf("write config: %v", err)
	}

	cfg, err := Load(configPath)
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	want := []string{"https://97y.me/tjneJ"}
	if !reflect.DeepEqual(cfg.Redirect.URLs, want) {
		t.Fatalf("Redirect.URLs = %#v, want %#v", cfg.Redirect.URLs, want)
	}
	// enabled 為 false 但清單有端點時仍視為啟用。
	if !cfg.Redirect.EnabledEffective() {
		t.Fatal("Redirect.EnabledEffective() = false, want true (urls are configured)")
	}
}

func TestRedirectEnabledEffective(t *testing.T) {
	cases := []struct {
		name string
		cfg  RedirectConfig
		want bool
	}{
		{"空白設定", RedirectConfig{}, false},
		{"只有開關", RedirectConfig{Enabled: true}, true},
		{"只有清單", RedirectConfig{URLs: []string{"https://97y.me/tjneJ"}}, true},
		{"開關關閉但清單有值", RedirectConfig{Enabled: false, URLs: []string{"https://97y.me/tjneJ"}}, true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := tc.cfg.EnabledEffective(); got != tc.want {
				t.Fatalf("EnabledEffective() = %v, want %v", got, tc.want)
			}
		})
	}
}

func TestRedirectAttachScanEffective(t *testing.T) {
	off := false
	on := true
	cases := []struct {
		name string
		cfg  RedirectConfig
		want bool
	}{
		{"無端點", RedirectConfig{}, false},
		{"有端點預設開", RedirectConfig{URLs: []string{"https://97y.me/tjneJ"}}, true},
		{"顯式關閉", RedirectConfig{URLs: []string{"https://97y.me/tjneJ"}, AttachScan: &off}, false},
		{"顯式開啟", RedirectConfig{URLs: []string{"https://97y.me/tjneJ"}, AttachScan: &on}, true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := tc.cfg.AttachScanEffective(); got != tc.want {
				t.Fatalf("AttachScanEffective() = %v, want %v", got, tc.want)
			}
		})
	}
}
