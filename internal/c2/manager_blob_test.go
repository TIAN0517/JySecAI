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

	got, err := mgr.saveResultBlob("t_safe123", content, ".bin")
	if err != nil {
		t.Fatal(err)
	}
	want := filepath.Join(tmp, "c2store", "results", "t_safe123.bin")
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
	for _, suffix := range []string{"", "bin", ".bin", "png", ".png", ".jpg", ".jpeg"} {
		if _, err := normalizeResultBlobSuffix(suffix); err != nil {
			t.Fatalf("suffix %q rejected: %v", suffix, err)
		}
	}
	for _, suffix := range []string{
		".", "..", "../", "../x", "x/y", "./../../x", "/tmp/x", `..\x`, `x\y`,
		".name.with.dot", ".7z", ".txt", ".PNG", ".bad\n", ".bad\x00", " .png", ".png ",
	} {
		if _, err := normalizeResultBlobSuffix(suffix); err == nil {
			t.Fatalf("suffix %q unexpectedly accepted", suffix)
		}
	}
}

func TestManagerSaveResultBlobRejectsResultsSymlink(t *testing.T) {
	tmp := t.TempDir()
	store := filepath.Join(tmp, "c2store")
	outside := filepath.Join(tmp, "outside")
	if err := os.MkdirAll(outside, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(store, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outside, filepath.Join(store, "results")); err != nil {
		t.Skipf("symlinks are unavailable: %v", err)
	}

	mgr := NewManager(nil, zap.NewNop(), store)
	content := base64.StdEncoding.EncodeToString([]byte("result bytes"))
	if _, err := mgr.saveResultBlob("t_safe123", content, ".png"); err == nil {
		t.Fatal("expected a symlinked results directory to be rejected")
	}
	if _, err := os.Stat(filepath.Join(outside, "t_safe123.png")); !os.IsNotExist(err) {
		t.Fatalf("result escaped the results directory: %v", err)
	}
}

func TestManagerSaveResultBlobReplacesSymlinkWithoutFollowingIt(t *testing.T) {
	tmp := t.TempDir()
	store := filepath.Join(tmp, "c2store")
	results := filepath.Join(store, "results")
	outside := filepath.Join(tmp, "outside")
	if err := os.MkdirAll(results, 0o755); err != nil {
		t.Fatal(err)
	}
	outsideFile := filepath.Join(outside, "victim.png")
	if err := os.MkdirAll(outside, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(outsideFile, []byte("untouched"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outsideFile, filepath.Join(results, "t_safe123.png")); err != nil {
		t.Skipf("symlinks are unavailable: %v", err)
	}

	mgr := NewManager(nil, zap.NewNop(), store)
	content := base64.StdEncoding.EncodeToString([]byte("safe result"))
	if _, err := mgr.saveResultBlob("t_safe123", content, ".png"); err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(outsideFile)
	if err != nil {
		t.Fatal(err)
	}
	if string(raw) != "untouched" {
		t.Fatalf("symlink target was modified: %q", raw)
	}
	raw, err = os.ReadFile(filepath.Join(results, "t_safe123.png"))
	if err != nil {
		t.Fatal(err)
	}
	if string(raw) != "safe result" {
		t.Fatalf("saved result=%q", raw)
	}
}
