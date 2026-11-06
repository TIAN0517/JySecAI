package security

import (
	"crypto/sha256"
	"crypto/subtle"
	"encoding/hex"
	"fmt"
	"strings"

	"golang.org/x/crypto/bcrypt"
)

// Platform permissions use module:action naming. They are intentionally
// separate from AI testing roles under roles/.
var PermissionCatalog = map[string]string{
	"auth:self":           "Manage own session and password",
	"dashboard:read":      "View dashboard summaries",
	"chat:read":           "View conversations",
	"chat:write":          "Create and update conversations",
	"chat:delete":         "Delete conversations and turns",
	"agent:execute":       "Run AI agents and workflows",
	"agent:local-execute": "Use local filesystem, shell, and configured command tools from an agent",
	"hitl:read":           "View HITL queues and logs",
	"hitl:write":          "Approve, dismiss, and configure HITL",
	// 授權狀態機（scope registry）：讀取與變更分開。
	// 核准授權券等於改變安全邊界本身，刻意不併入 hitl:write——
	// 兩者的 blast radius 不同，必須能單獨撤銷。
	"scope:read":           "View scope registry targets, grants, and coverage audit",
	"scope:write":          "Draft, approve, and revoke scope authorization grants",
	"tasks:read":           "View task queues",
	"tasks:write":          "Create and run task queues",
	"tasks:delete":         "Delete task queues",
	"project:read":         "View projects and project facts",
	"project:write":        "Create and update projects and facts",
	"project:delete":       "Delete projects and facts",
	"vulnerability:read":   "View vulnerabilities",
	"vulnerability:write":  "Create and update vulnerabilities",
	"vulnerability:delete": "Delete vulnerabilities",
	// 資料提取：把漏洞匯出成報告、URL 清單或完整記錄。
	// 刻意與 vulnerability:read 分開 —— 能看不等於能把整包資料帶走，
	// 匯出權限要能單獨撤銷、單獨指派。
	"vulnerability:export": "Export vulnerability data (reports, URLs, and full records)",
	"asset:read":           "View managed assets and asset summaries",
	"asset:write":          "Create, import, and update assets",
	"asset:delete":         "Delete managed assets",
	// 貸款案件主檔：來自靶場匯出的真實財務／個資資料（含匯出功能）。
	// 預設只給 admin —— 這是全平台敏感度最高的一組唯讀資料，
	// 要給 operator 請在 RBAC 介面個別指派。
	"loan:read":  "View loan case master data (read-only bridge)",
	"loan:write": "Modify loan case master data",
	// 通用提取記錄：掃描器從靶站抽出的資料（貸款案件／快遞訂單／帳號憑證／
	// 個人資料…）。讀取、寫入、匯出分開：能看列表不等於能把整包資料帶走。
	"records:read":    "View extracted records (typed, paginated)",
	"records:write":   "Ingest extracted records (automatic deduplication)",
	"records:export":  "Export extracted records (CSV)",
	"webshell:read":   "View WebShell connections",
	"webshell:write":  "Manage and use WebShell connections",
	"webshell:delete": "Delete WebShell connections",
	// Governs requests that omit connection_id and therefore supply their own
	// url/password. Those bypass the per-connection ownership ACL, so the
	// capability is reserved for admins rather than riding on webshell:write.
	"webshell:connect-unsaved": "Test unsaved WebShell connections against arbitrary URLs",
	"c2:read":                  "View C2 listeners, sessions, tasks, events, and profiles",
	"c2:write":                 "Operate C2 listeners, sessions, tasks, payloads, files, and profiles",
	"c2:delete":                "Delete C2 objects",
	"xss:read":                 "View XSS payloads, captures, and configuration",
	"xss:write":                "Create, update, and manage XSS payloads and captures",
	"xss:delete":               "Delete XSS payloads and all associated captures",
	"mcp:read":                 "View MCP status and external MCP configuration",
	"mcp:execute":              "Invoke the authenticated MCP endpoint",
	"mcp:external:execute":     "Invoke tools exposed by configured external MCP servers",
	"mcp:write":                "Manage external MCP server configuration and lifecycle",
	"knowledge:read":           "View knowledge base and retrieval logs",
	"knowledge:write":          "Create, update, index, and scan knowledge base",
	"knowledge:delete":         "Delete knowledge items and retrieval logs",
	"skills:read":              "View skills and skill stats",
	"skills:write":             "Create and update skills",
	"skills:delete":            "Delete skills and stats",
	"agents:read":              "View markdown agents",
	"agents:write":             "Create and update markdown agents",
	"agents:delete":            "Delete markdown agents",
	"roles:read":               "View AI testing roles",
	"roles:write":              "Create and update AI testing roles",
	"roles:delete":             "Delete AI testing roles",
	"workflow:read":            "View workflow definitions and runs",
	"workflow:execute":         "Validate, dry-run, and resume authorized workflow runs",
	"workflow:write":           "Create and update workflow definitions",
	"workflow:delete":          "Delete workflows",
	"config:read":              "View system configuration",
	"config:write":             "Update and apply system configuration",
	"terminal:execute":         "Run terminal commands",
	"audit:read":               "View and export audit logs",
	"audit:delete":             "Delete audit logs",
	"rbac:read":                "View users, platform roles, permissions, and assignments",
	"rbac:write":               "Manage users, platform roles, permissions, and assignments",
	"notification:read":        "View notifications",
	"notification:write":       "Mark notifications as read",
	"robot:read":               "View robot binding status",
	"robot:write":              "Manage robot bindings and test robot callbacks",
	"files:read":               "View chat uploads",
	"files:write":              "Upload, edit, and rename chat files",
	"files:delete":             "Delete chat files",
	"attackchain:read":         "View attack chains",
	"attackchain:write":        "Regenerate attack chains",
	"fofa:execute":             "Run FOFA searches and query parsing",
	"openapi:read":             "Read OpenAPI aggregation results",
	"monitor:read":             "View execution monitor",
	"monitor:write":            "Cancel monitor executions",
	"monitor:delete":           "Delete monitor executions",
}

func HashPassword(password string) (string, error) {
	password = strings.TrimSpace(password)
	if password == "" {
		return "", fmt.Errorf("password is empty")
	}
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", err
	}
	return string(hash), nil
}

func VerifyPasswordHash(password, encoded string) bool {
	if strings.HasPrefix(encoded, "$2a$") || strings.HasPrefix(encoded, "$2b$") || strings.HasPrefix(encoded, "$2y$") {
		return bcrypt.CompareHashAndPassword([]byte(encoded), []byte(strings.TrimSpace(password))) == nil
	}
	parts := strings.Split(encoded, "$")
	if len(parts) != 3 || parts[0] != "sha256" {
		return false
	}
	salt, err := hex.DecodeString(parts[1])
	if err != nil {
		return false
	}
	expected, err := hex.DecodeString(parts[2])
	if err != nil {
		return false
	}
	sum := sha256.Sum256(append(salt, []byte(strings.TrimSpace(password))...))
	return subtle.ConstantTimeCompare(sum[:], expected) == 1
}
