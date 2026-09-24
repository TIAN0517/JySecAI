package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"jysecai/internal/config"
)

func TestRaceRegression_MCPNormalizedBeforeAsyncPublication(t *testing.T) {
	t.Setenv("JY_RACE_FIXTURE", "expanded-fixture")
	received := make(chan string, 1)
	stub := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		select {
		case received <- r.Header.Get("X-Fixture"):
		default:
		}
		// A benign local transport failure, no MCP tools or external operations.
		w.WriteHeader(http.StatusServiceUnavailable)
	}))
	defer stub.Close()
	t.Setenv("JY_RACE_URL", stub.URL)
	router, handler, configPath := setupTestRouter()
	defer cleanupTestConfig(configPath)
	defer handler.manager.StopAll()
	body, err := json.Marshal(AddOrUpdateExternalMCPRequest{Config: config.ExternalMCPServerConfig{
		Type: "http", URL: "${JY_RACE_URL}", Headers: map[string]string{"X-Fixture": "${JY_RACE_FIXTURE}"},
		Timeout: 1, // Omitted enable flag retains the handler's existing default-enabled policy.
	}})
	if err != nil {
		t.Fatal(err)
	}
	req := httptest.NewRequest("PUT", "/api/external-mcp/fixture", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("status %d", w.Code)
	}
	published := handler.manager.GetConfigs()["fixture"]
	if published.URL != stub.URL || published.Headers["X-Fixture"] != "expanded-fixture" || !published.ExternalMCPEnable {
		t.Fatal("manager received unnormalized config")
	}
	select {
	case header := <-received:
		if header != "expanded-fixture" {
			t.Fatal("transport read unexpanded header")
		}
	case <-time.After(2 * time.Second):
		t.Fatal("local transport did not receive initialized config")
	}
}

func TestRaceRegression_MCPDisabledSnapshotOwnership(t *testing.T) {
	t.Setenv("JY_RACE_ARG", "expanded-fixture")
	router, handler, configPath := setupTestRouter()
	defer cleanupTestConfig(configPath)
	defer handler.manager.StopAll()
	body, err := json.Marshal(AddOrUpdateExternalMCPRequest{Config: config.ExternalMCPServerConfig{
		Command: "unused-local-fixture", Args: []string{"${JY_RACE_ARG}"},
		Env:      map[string]string{"fixture": "${JY_RACE_ARG}"},
		Disabled: true, ExternalMCPEnable: true,
	}})
	if err != nil {
		t.Fatal(err)
	}
	req := httptest.NewRequest("PUT", "/api/external-mcp/fixture", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("status %d", w.Code)
	}
	cfg := handler.manager.GetConfigs()["fixture"]
	if cfg.ExternalMCPEnable || !cfg.Disabled || cfg.Args[0] != "expanded-fixture" || cfg.Env["fixture"] != "expanded-fixture" {
		t.Fatal("disabled/expanded config was not consistently published")
	}
	if _, exists := handler.manager.GetClient("fixture"); exists {
		t.Fatal("disabled client started")
	}
	// The persisted handler config and manager config have distinct ownership.
	owned := handler.config.ExternalMCP.Servers["fixture"]
	owned.Args[0] = "handler-edited"
	owned.Env["fixture"] = "handler-edited"
	after := handler.manager.GetConfigs()["fixture"]
	if after.Args[0] != "expanded-fixture" || after.Env["fixture"] != "expanded-fixture" {
		t.Fatal("handler config aliases manager config")
	}
}
