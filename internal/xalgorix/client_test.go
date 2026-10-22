package xalgorix

import (
	"context"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestNewClientRejectsMetadataAndCredentials(t *testing.T) {
	for _, raw := range []string{
		"http://169.254.169.254/latest",
		"http://user:pass@127.0.0.1:9137",
		"ftp://127.0.0.1/scan",
		"",
	} {
		if _, err := NewClient(raw, "token"); err == nil {
			t.Fatalf("NewClient(%q) succeeded", raw)
		}
	}
	client, err := NewClient("http://127.0.0.1:9137", "token")
	if err != nil {
		t.Fatal(err)
	}
	if client.Host() != "127.0.0.1" {
		t.Fatalf("host = %s", client.Host())
	}
}

func TestClientDoesNotFollowRedirectOrLeakToken(t *testing.T) {
	var sawAuth string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		sawAuth = r.Header.Get("Authorization")
		if r.URL.Path == "/api/status" {
			http.Redirect(w, r, "http://169.254.169.254/latest", http.StatusFound)
			return
		}
		w.WriteHeader(http.StatusNotFound)
	}))
	defer server.Close()

	client, err := NewClient(server.URL, "secret-token")
	if err != nil {
		t.Fatal(err)
	}
	_, err = client.Status(context.Background())
	if err == nil || !strings.Contains(err.Error(), "重定向") {
		t.Fatalf("status error = %v", err)
	}
	if sawAuth != "Bearer secret-token" {
		t.Fatalf("auth header = %q", sawAuth)
	}
}

func TestStartScanPostsJSONWithoutTokenInBody(t *testing.T) {
	var body string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		body = string(raw)
		if r.URL.Path != "/api/scan" || r.Header.Get("Authorization") == "" {
			t.Errorf("path %s auth %q", r.URL.Path, r.Header.Get("Authorization"))
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"status":"started","instance_id":"inst_01"}`))
	}))
	defer server.Close()

	client, err := NewClient(server.URL, "secret-token")
	if err != nil {
		t.Fatal(err)
	}
	got, err := client.StartScan(context.Background(), map[string]any{"targets": []string{"https://app.example.com"}})
	if err != nil {
		t.Fatal(err)
	}
	if got["instance_id"] != "inst_01" {
		t.Fatalf("response %#v", got)
	}
	if strings.Contains(body, "secret-token") {
		t.Fatalf("token leaked into body: %s", body)
	}
}
