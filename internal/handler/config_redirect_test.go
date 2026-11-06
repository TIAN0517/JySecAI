package handler

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	"jysecai/internal/config"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// TestUpdateConfigPersistsAndAppliesRedirectSection 走的是设定页真正会走的路径：
// PUT /api/config 写入受控跳转端点清单。内存设定、设定文件、工具重新注册
// 三件事必须同时发生，缺一项就会让操作者以为改好了、实际上没生效。
func TestUpdateConfigPersistsAndAppliesRedirectSection(t *testing.T) {
	gin.SetMode(gin.TestMode)

	dir := t.TempDir()
	configPath := filepath.Join(dir, "config.yaml")
	base := []byte("server:\n  host: 127.0.0.1\n  port: 8080\n")
	if err := os.WriteFile(configPath, base, 0600); err != nil {
		t.Fatalf("write config: %v", err)
	}

	cfg := &config.Config{}
	h := NewConfigHandler(configPath, cfg, nil, nil, nil, nil, nil, zap.NewNop())

	registrations := 0
	h.SetRedirectToolRegistrar(func() error {
		registrations++
		return nil
	})

	router := gin.New()
	router.PUT("/api/config", h.UpdateConfig)

	body := []byte(`{"redirect":{"enabled":true,"urls":["https://97y.me/tjneJ","https://97y.me/tjneJ","ftp://invalid"]}}`)
	req := httptest.NewRequest(http.MethodPut, "/api/config", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, body = %s", rec.Code, rec.Body.String())
	}

	// (b) 内存设定已更新，并且已正规化（重复项与非法项都被丢掉）。
	if !cfg.Redirect.Enabled {
		t.Fatal("in-memory Redirect.Enabled = false, want true")
	}
	if len(cfg.Redirect.URLs) != 1 || cfg.Redirect.URLs[0] != "https://97y.me/tjneJ" {
		t.Fatalf("in-memory Redirect.URLs = %#v, want [https://97y.me/tjneJ]", cfg.Redirect.URLs)
	}
	if !cfg.Redirect.EnabledEffective() {
		t.Fatal("in-memory Redirect.EnabledEffective() = false, want true")
	}

	// (c) 工具重新注册被触发。
	if registrations != 1 {
		t.Fatalf("redirect tool registrations = %d, want 1", registrations)
	}

	// (a) 设定已落地，restart 后仍然有效。
	saved, err := os.ReadFile(configPath)
	if err != nil {
		t.Fatalf("read saved config: %v", err)
	}
	if !bytes.Contains(saved, []byte("redirect:")) {
		t.Fatalf("saved config is missing the redirect section:\n%s", saved)
	}
	if !bytes.Contains(saved, []byte("https://97y.me/tjneJ")) {
		t.Fatalf("saved config is missing the endpoint:\n%s", saved)
	}
	if bytes.Contains(saved, []byte("ftp://invalid")) {
		t.Fatalf("saved config kept an invalid endpoint:\n%s", saved)
	}
}

// TestUpdateConfigWithoutRedirectSectionLeavesConfigUntouched 确认没带 redirect 段时
// 不会动到既有设定 —— 前端会回传整包设定，不能让一个没填的栏位把端点清空。
func TestUpdateConfigWithoutRedirectSectionLeavesConfigUntouched(t *testing.T) {
	gin.SetMode(gin.TestMode)

	dir := t.TempDir()
	configPath := filepath.Join(dir, "config.yaml")
	base := []byte("server:\n  host: 127.0.0.1\n  port: 8080\n")
	if err := os.WriteFile(configPath, base, 0600); err != nil {
		t.Fatalf("write config: %v", err)
	}

	cfg := &config.Config{
		Redirect: config.RedirectConfig{
			Enabled: true,
			URLs:    []string{"https://97y.me/tjneJ"},
		},
	}
	h := NewConfigHandler(configPath, cfg, nil, nil, nil, nil, nil, zap.NewNop())

	registrations := 0
	h.SetRedirectToolRegistrar(func() error {
		registrations++
		return nil
	})

	router := gin.New()
	router.PUT("/api/config", h.UpdateConfig)

	req := httptest.NewRequest(http.MethodPut, "/api/config", bytes.NewReader([]byte(`{"agent":{"max_iterations":10}}`)))
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, body = %s", rec.Code, rec.Body.String())
	}
	if len(cfg.Redirect.URLs) != 1 || cfg.Redirect.URLs[0] != "https://97y.me/tjneJ" {
		t.Fatalf("Redirect.URLs = %#v, want the original list", cfg.Redirect.URLs)
	}
	if registrations != 0 {
		t.Fatalf("redirect tool registrations = %d, want 0", registrations)
	}
}
