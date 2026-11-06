package handler

import (
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/gin-gonic/gin"
)

// MountGovernancePage 把 2026-09 的控制面頁面掛回主服務。
//
// 當時 /governance/ 是由 nginx 轉到獨立的 control-plane:8787。
// eacffacdc 清掉那套程序與 nginx 後，頁首按鈕仍指向 /governance/，
// 主服務沒有這條路由，Gin 就回 404 page not found。
//
// 這裡只恢復頁面與唯讀狀態。建立任務、審批、Stripe 結帳屬於已移除的
// 控制面，不能在主服務上假裝還能下單或開掃。
func MountGovernancePage(router *gin.Engine, root string) {
	if root == "" {
		root = filepath.Join("web", "governance")
	}
	router.GET("/governance", func(c *gin.Context) {
		c.Redirect(http.StatusPermanentRedirect, "/governance/")
	})
	router.Static("/governance/assets", filepath.Join(root, "assets"))
	router.GET("/governance/", func(c *gin.Context) {
		page := filepath.Join(root, "index.html")
		if _, err := os.Stat(page); err != nil {
			c.String(http.StatusNotFound, "governance page is not installed")
			return
		}
		c.File(page)
	})

	router.GET("/v1/catalog", governanceCatalog)
	router.GET("/v1/usage", governanceUsage)
	router.GET("/v1/billing/status", governanceBillingStatus)
	router.GET("/v1/runs", governanceRuns)
	router.GET("/v1/runs/:id/events", governanceEmptyEvents)
	router.GET("/v1/runs/:id/artifacts", governanceEmptyArtifacts)
	router.GET("/v1/projects/:id/findings", governanceEmptyFindings)
	router.POST("/v1/runs", governanceRetired)
	router.POST("/v1/runs/:id/approve", governanceRetired)
	router.POST("/v1/runs/:id/cancel", governanceRetired)
	router.POST("/v1/billing/checkout", governanceRetired)
	router.POST("/v1/billing/portal", governanceRetired)
}

func governanceRetired(c *gin.Context) {
	c.JSON(http.StatusGone, gin.H{
		"error": gin.H{
			"code":    "control_plane_retired",
			"message": "獨立控制面已於清理舊版部署時移除。此頁只顯示狀態，不能建立任務或進行結帳。",
		},
	})
}

func governanceCatalog(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"product": gin.H{
			"name":         "JySecAI",
			"developer":    "Jy 技術團隊",
			"architecture": "governed multi-engine security orchestration",
		},
		"engines": governanceEngines(),
		"plans":   governancePlans(),
	})
}

func governanceUsage(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"period":      time.Now().UTC().Format("2006-01"),
		"plan":        governancePlans()[0],
		"usedCredits": 0,
	})
}

func governanceBillingStatus(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"enabled":          false,
		"subscription":     nil,
		"selfServicePlans": []string{"professional", "business"},
	})
}

func governanceRuns(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"items": []any{}})
}

func governanceEmptyEvents(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"events": []any{}})
}

func governanceEmptyArtifacts(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"artifacts": []any{}})
}

func governanceEmptyFindings(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"findings": []any{}})
}

func governancePlans() []gin.H {
	return []gin.H{
		{"id": "community", "displayName": "Community", "monthlyCredits": 50, "maxConcurrentRuns": 1, "auditRetentionDays": 7},
		{"id": "professional", "displayName": "Professional", "monthlyCredits": 2500, "maxConcurrentRuns": 5, "auditRetentionDays": 90},
		{"id": "business", "displayName": "Business", "monthlyCredits": 20000, "maxConcurrentRuns": 25, "auditRetentionDays": 365},
		{"id": "enterprise", "displayName": "Enterprise Sovereign", "monthlyCredits": 100000, "maxConcurrentRuns": 100, "auditRetentionDays": 2555},
	}
}

func governanceEngines() []gin.H {
	type engine struct {
		id, name, category, maturity, operation, connector, description string
		operations                                                      []string
	}
	defs := []engine{
		{"strix", "Strix Autonomous Pentest", "appsec", "core", "active_scan", "worker", "Sandboxed autonomous application, API and source security validation.", []string{"active_scan", "exploit_validation", "source_review"}},
		{"jysecai", "Jy Workflow Orchestrator", "appsec", "core", "active_scan", "http", "Governed project, workflow, evidence and attack-chain execution plane.", []string{"passive_discovery", "active_scan", "exploit_validation", "credential_audit", "source_review"}},
		{"hexstrike", "HexStrike AI", "appsec", "optional", "active_scan", "worker", "Remote Kali tool orchestration with normalized findings and conditional validation tasks.", []string{"passive_discovery", "active_scan", "exploit_validation", "credential_audit"}},
		{"kali-mcp", "MCP Kali Server", "appsec", "optional", "active_scan", "worker", "TriV3 Kali API and MCP tool fabric with governed execution and evidence ingestion.", []string{"passive_discovery", "active_scan", "exploit_validation", "credential_audit"}},
		{"promptfoo", "Promptfoo CI Red Team", "ai-security", "core", "ai_red_team", "worker", "Repeatable LLM, RAG and prompt-security regression testing.", []string{"ai_red_team"}},
		{"pyrit", "PyRIT Campaign", "ai-security", "core", "ai_red_team", "worker", "Multi-turn and multimodal generative-AI risk campaign orchestration.", []string{"ai_red_team"}},
		{"giskard", "Giskard Agent Evaluation", "ai-security", "core", "ai_red_team", "worker", "Dynamic agent and RAG quality, safety and regression evaluation.", []string{"ai_red_team"}},
		{"art", "Adversarial Robustness Toolbox", "ml-security", "core", "ai_red_team", "worker", "Isolated CPU/GPU adversarial machine-learning robustness evaluation.", []string{"ai_red_team"}},
		{"humanbound", "Humanbound Agent Boundary", "ai-security", "optional", "ai_red_team", "worker", "Agent tool-boundary, indirect-injection and permission-abuse testing.", []string{"ai_red_team"}},
		{"ad-audit", "Active Directory Risk Audit", "identity", "core", "credential_audit", "worker", "Read-only SPN, Kerberos encryption, pre-authentication and event analytics.", []string{"credential_audit"}},
	}
	out := make([]gin.H, 0, len(defs))
	for _, item := range defs {
		out = append(out, gin.H{
			"id":                  item.id,
			"name":                item.name,
			"category":            item.category,
			"maturity":            item.maturity,
			"profiles":            []string{"quick", "standard"},
			"requiredOperation":   item.operation,
			"supportedOperations": item.operations,
			"connector":           item.connector,
			"description":         item.description,
			"active":              false,
			"status":              "unconfigured",
			"reason":              "獨立控制面已移除，此引擎沒有掛在目前的 jysec-core 上。",
		})
	}
	return out
}
