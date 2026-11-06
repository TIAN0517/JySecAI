package handler

import (
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"jysecai/internal/database"
)

// TestReadWebshellBodyBoundsUnlimitedStream is the regression guard for the
// operator-triggerable OOM. webshell:write is granted to the operator role, so
// any operator could point a connection at a peer that never stops sending and
// take down the process for every other user.
func TestReadWebshellBodyBoundsUnlimitedStream(t *testing.T) {
	// A body far larger than the cap, produced without allocating it all.
	pr, pw := io.Pipe()
	go func() {
		defer pw.Close()
		chunk := strings.Repeat("A", 1<<20) // 1 MiB
		for i := 0; i < 64; i++ {           // 64 MiB total
			if _, err := pw.Write([]byte(chunk)); err != nil {
				return
			}
		}
	}()
	defer pr.Close()

	out, truncated, err := readWebshellBody(pr)
	if err != nil {
		t.Fatalf("readWebshellBody: %v", err)
	}
	if !truncated {
		t.Error("truncated = false for a 64 MiB body over a 32 MiB cap")
	}
	if len(out) != maxWebshellResponseBytes {
		t.Errorf("len(out) = %d, want exactly %d", len(out), maxWebshellResponseBytes)
	}
}

func TestReadWebshellBodyPassesSmallResponsesThrough(t *testing.T) {
	for _, size := range []int{0, 1, 1024, maxWebshellResponseBytes - 1, maxWebshellResponseBytes} {
		body := strings.Repeat("x", size)
		out, truncated, err := readWebshellBody(strings.NewReader(body))
		if err != nil {
			t.Fatalf("size %d: %v", size, err)
		}
		if truncated {
			t.Errorf("size %d: reported truncation at or below the cap", size)
		}
		if len(out) != size {
			t.Errorf("size %d: got %d bytes back", size, len(out))
		}
	}
	// One byte over the cap must truncate, not silently drop the tail.
	body := strings.Repeat("x", maxWebshellResponseBytes+1)
	out, truncated, err := readWebshellBody(strings.NewReader(body))
	if err != nil {
		t.Fatal(err)
	}
	if !truncated || len(out) != maxWebshellResponseBytes {
		t.Errorf("cap+1: truncated=%v len=%d", truncated, len(out))
	}
}

// TestWebshellExecTruncatesHostileTarget drives the real handler end to end
// against a server that streams without end, which is the actual attack.
func TestWebshellExecTruncatesHostileTarget(t *testing.T) {
	stream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain")
		flusher, _ := w.(http.Flusher)
		chunk := strings.Repeat("B", 1<<20)
		for i := 0; i < 40; i++ { // 40 MiB
			if _, err := w.Write([]byte(chunk)); err != nil {
				return
			}
			if flusher != nil {
				flusher.Flush()
			}
		}
	}))
	defer stream.Close()

	h := newTestWebShellHandler()
	rec := performWebshellJSONWithPerms(
		&database.RBACUser{ID: "u1", Username: "op"},
		http.MethodPost, "/api/webshell/exec",
		map[string]interface{}{"url": stream.URL, "type": "php", "command": "id"},
		h.Exec,
		// Omitting connection_id is the ad-hoc path, which the RBAC fix
		// deliberately reserves for callers holding this permission.
		map[string]bool{"webshell:connect-unsaved": true},
	)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, body = %.200s", rec.Code, rec.Body.String())
	}
	body := rec.Body.String()
	if len(body) > maxWebshellResponseBytes+(1<<16) {
		t.Errorf("response body is %d bytes; the cap did not bound it", len(body))
	}
	if !strings.Contains(body, "已截断") {
		t.Errorf("operator was not told the output was truncated; body head: %.200s", body)
	}
}
