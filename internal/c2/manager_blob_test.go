package c2

import (
	"encoding/base64"
	"os"
	"path/filepath"
	"testing"

	"go.uber.org/zap"
)

func TestManagerSaveResultBlobConfinesPath(t *testing.T) {
	tmp := t.TempDir()
	mgr := NewManager(nil, zap.NewNop(), filepath.Join(tmp, "c2store"))
	content := base64.StdEncoding.EncodeToString([]byte("result bytes"))

	got, err := mgr.saveResultBlob("t_safe123", content, "png")
	if err != nil {
		t.Fatal(err)
	}
	want := filepath.Join(tmp, "c2store", "results", "t_safe123.png")
	if got != want {
		t.Fatalf("path=%q want %q", got, want)
	}
	raw, err := os.ReadFile(want)
	if err != nil {
		t.Fatal(err)
	}
	if string(raw) != "result bytes" {
		t.Fatalf("content=%q", raw)
	}

	outside := filepath.Join(tmp, "owned")
	if _, err := mgr.saveResultBlob("t_safe123", content, "./../../owned"); err == nil {
		t.Fatal("expected traversal suffix to be rejected")
	}
	if _, err := os.Stat(outside); !os.IsNotExist(err) {
		t.Fatalf("outside file exists or stat failed unexpectedly: %v", err)
	}
}

func TestUploadPathForTaskConfinesPath(t *testing.T) {
	tmp := t.TempDir()
	store := filepath.Join(tmp, "c2store")

	dir, got, err := uploadPathForTask(store, "t_safe123")
	if err != nil {
		t.Fatal(err)
	}
	if want := filepath.Join(store, "uploads"); dir != want {
		t.Fatalf("dir=%q want %q", dir, want)
	}
	if want := filepath.Join(store, "uploads", "t_safe123.bin"); got != want {
		t.Fatalf("path=%q want %q", got, want)
	}

	for _, taskID := range []string{"", ".", "..", "../owned", `..\owned`, "sub/owned", "sub\\owned", "task.with.dot", "-leading"} {
		if _, _, err := uploadPathForTask(store, taskID); err == nil {
			t.Fatalf("task_id %q unexpectedly accepted", taskID)
		}
	}
}

func TestNormalizeResultBlobSuffix(t *testing.T) {
	for suffix, want := range map[string]string{"": ".bin", "png": ".png", ".PNG": ".png", ".jpg": ".jpg", "jpeg": ".jpeg", ".bin": ".bin"} {
		if got, err := normalizeResultBlobSuffix(suffix); err != nil {
			t.Fatalf("suffix %q rejected: %v", suffix, err)
		} else if got != want {
			t.Fatalf("suffix %q normalized to %q, want %q", suffix, got, want)
		}
	}
	for _, suffix := range []string{".", "..", "../x", "./../../x", "/tmp/x", `..\x`, ".name.with.dot", ".7z", ".svg", ".html", ".txt", ".safe_name-1"} {
		if _, err := normalizeResultBlobSuffix(suffix); err == nil {
			t.Fatalf("suffix %q unexpectedly accepted", suffix)
		}
	}
}

func TestManagerSaveResultBlobRejectsSymlinks(t *testing.T) {
	t.Run("results directory symlink", func(t *testing.T) {
		tmp := t.TempDir()
		store := filepath.Join(tmp, "store")
		outside := filepath.Join(tmp, "outside")
		if err := os.MkdirAll(store, 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.MkdirAll(outside, 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.Symlink(outside, filepath.Join(store, "results")); err != nil {
			t.Skipf("symlinks unavailable: %v", err)
		}
		mgr := NewManager(nil, zap.NewNop(), store)
		content := base64.StdEncoding.EncodeToString([]byte("must stay confined"))
		if _, err := mgr.saveResultBlob("t_symlink_dir", content, ".bin"); err == nil {
			t.Fatal("expected symlinked results directory to be rejected")
		}
		if _, err := os.Stat(filepath.Join(outside, "t_symlink_dir.bin")); !os.IsNotExist(err) {
			t.Fatalf("outside file exists or stat failed unexpectedly: %v", err)
		}
	})

	t.Run("destination symlink", func(t *testing.T) {
		tmp := t.TempDir()
		store := filepath.Join(tmp, "store")
		results := filepath.Join(store, "results")
		if err := os.MkdirAll(results, 0o755); err != nil {
			t.Fatal(err)
		}
		outside := filepath.Join(tmp, "outside.bin")
		if err := os.WriteFile(outside, []byte("original"), 0o600); err != nil {
			t.Fatal(err)
		}
		if err := os.Symlink(outside, filepath.Join(results, "t_symlink_file.bin")); err != nil {
			t.Skipf("symlinks unavailable: %v", err)
		}
		mgr := NewManager(nil, zap.NewNop(), store)
		content := base64.StdEncoding.EncodeToString([]byte("overwrite"))
		if _, err := mgr.saveResultBlob("t_symlink_file", content, ".bin"); err == nil {
			t.Fatal("expected destination symlink to be rejected")
		}
		raw, err := os.ReadFile(outside)
		if err != nil {
			t.Fatal(err)
		}
		if string(raw) != "original" {
			t.Fatalf("outside target was modified: %q", raw)
		}
	})
}
