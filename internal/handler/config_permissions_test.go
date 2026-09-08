package handler

import (
	"os"
	"path/filepath"
	"runtime"
	"testing"

	"jysecai/internal/config"
	"jysecai/internal/mcp"

	"go.uber.org/zap"
)

func TestConfigSaversUsePrivatePermissionsForConfigAndBackup(t *testing.T) {
	tests := []struct {
		name string
		save func(path string) error
	}{
		{
			name: "main config handler",
			save: func(path string) error {
				h := NewConfigHandler(path, &config.Config{}, nil, nil, nil, nil, nil, zap.NewNop())
				return h.saveConfig()
			},
		},
		{
			name: "external MCP handler",
			save: func(path string) error {
				h := NewExternalMCPHandler(mcp.NewExternalMCPManager(zap.NewNop()), &config.Config{}, path, zap.NewNop())
				return h.saveConfig()
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dir := t.TempDir()
			path := filepath.Join(dir, "config.yaml")
			backupPath := path + ".backup"
			original := []byte("ai:\n  channels:\n    private:\n      api_key: secret-value\n")
			if err := os.WriteFile(path, original, 0644); err != nil {
				t.Fatalf("write config: %v", err)
			}
			if err := os.Chmod(path, 0644); err != nil {
				t.Fatalf("chmod config: %v", err)
			}
			// Exercise replacement of an already-existing, overly broad backup.
			if err := os.WriteFile(backupPath, []byte("stale"), 0644); err != nil {
				t.Fatalf("write backup: %v", err)
			}
			if err := os.Chmod(backupPath, 0644); err != nil {
				t.Fatalf("chmod backup: %v", err)
			}

			if err := tt.save(path); err != nil {
				t.Fatalf("save config: %v", err)
			}

			assertPrivateFileMode(t, path)
			assertPrivateFileMode(t, backupPath)
			backup, err := os.ReadFile(backupPath)
			if err != nil {
				t.Fatalf("read backup: %v", err)
			}
			if string(backup) != string(original) {
				t.Fatalf("backup contents = %q, want original config", backup)
			}
		})
	}
}

func TestWriteYAMLDocumentCreatesPrivateFile(t *testing.T) {
	path := filepath.Join(t.TempDir(), "config.yaml")
	if err := writeYAMLDocument(path, newEmptyYAMLDocument()); err != nil {
		t.Fatalf("writeYAMLDocument: %v", err)
	}
	assertPrivateFileMode(t, path)
}

func assertPrivateFileMode(t *testing.T, path string) {
	t.Helper()
	info, err := os.Stat(path)
	if err != nil {
		t.Fatalf("stat %s: %v", path, err)
	}
	if runtime.GOOS == "windows" {
		// Windows has no POSIX mode bits: os.Chmod only toggles the read-only
		// attribute and Mode().Perm() always reports 0666/0444. The 0600
		// contract is enforced on POSIX platforms where it is representable.
		return
	}
	if got := info.Mode().Perm(); got != 0600 {
		t.Fatalf("%s permissions = %04o, want 0600", path, got)
	}
}
