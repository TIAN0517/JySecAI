package app

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"

	"jysecai/internal/authctx"
	"jysecai/internal/database"
	"jysecai/internal/handler"
	"jysecai/internal/mcp"
	"jysecai/internal/mcp/builtin"

	"go.uber.org/zap"
)

func setupAWVSToolsTest(t *testing.T, mockAWVSURL string) (*database.DB, *mcp.Server, *handler.AWVSHandler, string, context.Context) {
	t.Helper()
	tmp := t.TempDir()
	db, err := database.NewDB(filepath.Join(tmp, "awvs-tools-test.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })

	user, err := db.CreateRBACUser("awvs-tester", "AWVS Tester", "hash", true, nil)
	if err != nil {
		t.Fatal(err)
	}
	principal := authctx.NewPrincipal(user.ID, user.Username, database.RBACScopeAll, map[string]bool{
		"vulnerability:read": true, "vulnerability:write": true,
	})
	ctx := authctx.WithPrincipal(context.Background(), principal)

	conversation, err := db.CreateConversation("awvs conv", database.ConversationCreateMeta{})
	if err != nil {
		t.Fatal(err)
	}

	awvsHandler := handler.NewAWVSHandler(db, zap.NewNop(), mockAWVSURL, "test-api-token")
	server := mcp.NewServer(zap.NewNop())
	server.SetToolAuthorizer(mcpToolAuthorizer(db))
	registerAWVSTools(server, db, awvsHandler, zap.NewNop())

	return db, server, awvsHandler, conversation.ID, mcp.WithMCPConversationID(ctx, conversation.ID)
}

func TestAWVSToolsLifecycle(t *testing.T) {
	// 建立 Mock AWVS API 伺服器
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		switch r.URL.Path {
		case "/api/v1/me":
			_ = json.NewEncoder(w).Encode(map[string]interface{}{
				"email": "security-lead@example.com",
				"role":  "admin",
			})
		case "/api/v1/targets":
			_ = json.NewEncoder(w).Encode(map[string]interface{}{
				"targets": []map[string]interface{}{
					{
						"target_id":   "target-001",
						"address":     "https://app.target.com",
						"description": "Production App",
						"criticality": 10,
					},
				},
				"pagination": map[string]interface{}{"count": 1},
			})
		case "/api/v1/scans":
			if r.Method == http.MethodPost {
				w.WriteHeader(http.StatusCreated)
				_ = json.NewEncoder(w).Encode(map[string]interface{}{
					"scan_id":   "scan-created-123",
					"target_id": "target-001",
				})
			} else {
				_ = json.NewEncoder(w).Encode(map[string]interface{}{
					"scans": []map[string]interface{}{
						{
							"scan_id": "scan-existing-001",
							"target":  map[string]interface{}{"address": "https://app.target.com"},
							"current_session": map[string]interface{}{
								"status": "completed",
							},
							"profile_name": "Full Scan",
						},
					},
				})
			}
		case "/api/v1/scans/scan-existing-001":
			_ = json.NewEncoder(w).Encode(map[string]interface{}{
				"scan_id": "scan-existing-001",
				"target": map[string]interface{}{
					"address":     "https://app.target.com",
					"description": "Production App",
				},
				"current_session": map[string]interface{}{
					"status":   "completed",
					"progress": 100.0,
					"severity_counts": map[string]interface{}{
						"high":   2,
						"medium": 3,
						"low":    1,
						"info":   5,
					},
				},
			})
		case "/api/v1/vulnerabilities":
			_ = json.NewEncoder(w).Encode(map[string]interface{}{
				"vulnerabilities": []map[string]interface{}{
					{
						"vuln_id":     "vuln-awvs-1",
						"vt_name":     "Reflected Cross-Site Scripting (XSS)",
						"affects_url": "https://app.target.com/search?q=test",
						"severity":    3, // high
						"tags":        []string{"XSS"},
					},
				},
				"pagination": map[string]interface{}{"count": 1},
			})
		case "/api/v1/vulnerabilities/vuln-awvs-1":
			_ = json.NewEncoder(w).Encode(map[string]interface{}{
				"description":    "Target is vulnerable to reflected XSS",
				"request":        "GET /search?q=<script>alert(1)</script> HTTP/1.1\r\nHost: app.target.com\r\n\r\n",
				"impact":         "Session hijacking",
				"recommendation": "Encode all user inputs",
			})
		default:
			w.WriteHeader(http.StatusNotFound)
		}
	}))
	defer mockServer.Close()

	_, server, _, _, ctx := setupAWVSToolsTest(t, mockServer.URL)

	// 1. awvs_status
	resStatus, _, err := server.CallTool(ctx, builtin.ToolAWVSStatus, map[string]interface{}{})
	if err != nil {
		t.Fatalf("call awvs_status failed: %v", err)
	}
	if !strings.Contains(resStatus.Content[0].Text, "正常連線") || !strings.Contains(resStatus.Content[0].Text, "security-lead@example.com") {
		t.Errorf("expected connected status, got: %s", resStatus.Content[0].Text)
	}

	// 2. awvs_list_targets
	resTargets, _, err := server.CallTool(ctx, builtin.ToolAWVSListTargets, map[string]interface{}{})
	if err != nil {
		t.Fatalf("call awvs_list_targets failed: %v", err)
	}
	if !strings.Contains(resTargets.Content[0].Text, "https://app.target.com") || !strings.Contains(resTargets.Content[0].Text, "target-001") {
		t.Errorf("expected targets list, got: %s", resTargets.Content[0].Text)
	}

	// 3. awvs_start_scan
	resStart, _, err := server.CallTool(ctx, builtin.ToolAWVSStartScan, map[string]interface{}{
		"target_id": "target-001",
	})
	if err != nil {
		t.Fatalf("call awvs_start_scan failed: %v", err)
	}
	if !strings.Contains(resStart.Content[0].Text, "scan-created-123") {
		t.Errorf("expected scan_id scan-created-123, got: %s", resStart.Content[0].Text)
	}

	// 4. awvs_get_scan_status (單個)
	resGetScan, _, err := server.CallTool(ctx, builtin.ToolAWVSGetScanStatus, map[string]interface{}{
		"scan_id": "scan-existing-001",
	})
	if err != nil {
		t.Fatalf("call awvs_get_scan_status failed: %v", err)
	}
	if !strings.Contains(resGetScan.Content[0].Text, "COMPLETED") || !strings.Contains(resGetScan.Content[0].Text, "**高危 (High)**: 2") {
		t.Errorf("expected scan detail with 2 high vulns, got: %s", resGetScan.Content[0].Text)
	}

	// 5. awvs_sync_vulnerabilities
	resSync, _, err := server.CallTool(ctx, builtin.ToolAWVSSyncVulnerabilities, map[string]interface{}{})
	if err != nil {
		t.Fatalf("call awvs_sync_vulnerabilities failed: %v", err)
	}
	if !strings.Contains(resSync.Content[0].Text, "**新建立本機漏洞記錄**: 1 條") {
		t.Errorf("expected 1 vuln synced, got: %s", resSync.Content[0].Text)
	}
}
