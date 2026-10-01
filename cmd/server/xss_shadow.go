package main

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"jysecai/internal/database"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"time"
)

// This maintenance entry point deliberately bypasses config loading, NewDB's
// general migrations, authentication bootstrap, MCP, scanners and all workers.
// No original DB or production config is opened by it.
func runXSSShadow(path string, seconds int) error {
	if seconds < 0 || seconds > 30 {
		return errors.New("shadow health duration must be 0-30 seconds")
	}
	abs, err := filepath.Abs(path)
	if err != nil {
		return err
	}
	real, err := filepath.EvalSymlinks(abs)
	if err != nil {
		return err
	}
	if real != abs || filepath.Base(abs) != "shadow.db" {
		return errors.New("requires a non-symlink shadow.db")
	}
	marker, err := os.ReadFile(filepath.Join(filepath.Dir(abs), ".xss-shadow.json"))
	if err != nil {
		return err
	}
	var m struct {
		Shadow       string `json:"shadow"`
		Source       string `json:"source"`
		BackupSHA256 string `json:"backup_sha256"`
	}
	if err = json.Unmarshal(marker, &m); err != nil {
		return err
	}
	if m.Shadow != abs || m.Source == "" || m.Source == abs {
		return errors.New("shadow marker mismatch")
	}
	info, err := os.Stat(abs)
	if err != nil {
		return err
	}
	if original, e := os.Stat(m.Source); e == nil && os.SameFile(info, original) {
		return errors.New("shadow aliases production file")
	}
	backupPath := filepath.Join(filepath.Dir(abs), "production-backup.db")
	backupInfo, err := os.Stat(backupPath)
	if err != nil {
		return err
	}
	if os.SameFile(info, backupInfo) {
		return errors.New("shadow aliases immutable backup")
	}
	f, err := os.Open(backupPath)
	if err != nil {
		return err
	}
	h := sha256.New()
	_, err = io.Copy(h, f)
	f.Close()
	if err != nil {
		return err
	}
	if hex.EncodeToString(h.Sum(nil)) != m.BackupSHA256 {
		return errors.New("backup hash mismatch")
	}
	uri := url.URL{Scheme: "file", Path: filepath.ToSlash(abs), RawQuery: "mode=rw&_foreign_keys=on&_busy_timeout=5000"}
	raw, err := sql.Open("sqlite3", uri.String())
	if err != nil {
		return err
	}
	defer raw.Close()
	raw.SetMaxOpenConns(1)
	if err = database.MigrateXSSV2(context.Background(), raw); err != nil {
		return err
	}
	var payloads, captures int
	if err = raw.QueryRow("SELECT count(*) FROM xss_payloads").Scan(&payloads); err != nil {
		return err
	}
	if err = raw.QueryRow("SELECT count(*) FROM xss_captures").Scan(&captures); err != nil {
		return err
	}
	result := map[string]interface{}{"shadow": abs, "migration": "PASS", "payload_rows": payloads, "capture_rows": captures, "collector_enabled": false, "normal_application_started": false}
	if seconds > 0 {
		ln, err := net.Listen("tcp", "127.0.0.1:0")
		if err != nil {
			return err
		}
		mux := http.NewServeMux()
		mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Cache-Control", "no-store")
			w.Header().Set("X-Content-Type-Options", "nosniff")
			if r.Method != "GET" {
				w.WriteHeader(405)
				return
			}
			w.Header().Set("Content-Type", "application/json")
			io.WriteString(w, `{"mode":"xss-shadow","ok":true}`)
		})
		srv := &http.Server{Handler: mux, ReadHeaderTimeout: time.Second, WriteTimeout: time.Second}
		done := make(chan error, 1)
		go func() { done <- srv.Serve(ln) }()
		client := http.Client{Timeout: time.Second}
		resp, err := client.Get("http://" + ln.Addr().String() + "/health")
		if err != nil {
			srv.Close()
			return err
		}
		resp.Body.Close()
		if resp.StatusCode != 200 {
			srv.Close()
			return fmt.Errorf("health status %d", resp.StatusCode)
		}
		result["health_listener"] = ln.Addr().String()
		result["health_check"] = "PASS"
		time.Sleep(time.Duration(seconds) * time.Second)
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		err = srv.Shutdown(ctx)
		cancel()
		if err != nil {
			return err
		}
		if err = <-done; !errors.Is(err, http.ErrServerClosed) {
			return err
		}
		released, err := net.Listen("tcp", ln.Addr().String())
		if err != nil {
			return err
		}
		released.Close()
		result["port_released"] = true
	}
	return json.NewEncoder(os.Stdout).Encode(result)
}
