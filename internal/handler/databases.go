package handler

import (
	"context"
	"database/sql"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"jysecai/internal/config"

	"github.com/gin-gonic/gin"
)

// DatabasesHandler 提供平台本地 SQLite 目錄（唯讀），給「數據庫管理」頁使用。
type DatabasesHandler struct {
	cfg        *config.Config
	loan       *LoanHandler
	assetIntel *AssetIntelHandler
	records    *RecordsHandler
}

// WithRecords 掛上提取記錄庫，讓「數據庫管理」頁也列出它。
func (h *DatabasesHandler) WithRecords(r *RecordsHandler) *DatabasesHandler {
	if h != nil {
		h.records = r
	}
	return h
}

func NewDatabasesHandler(cfg *config.Config, loan *LoanHandler, assetIntel *AssetIntelHandler) *DatabasesHandler {
	return &DatabasesHandler{cfg: cfg, loan: loan, assetIntel: assetIntel}
}

func (h *LoanHandler) DBPath() string {
	if h == nil {
		return ""
	}
	return h.dbPath
}

func (h *AssetIntelHandler) DBPath() string {
	if h == nil {
		return ""
	}
	return h.dbPath
}

var platformFeatureTables = []string{
	"redirect_verify_runs",
	"redirect_verify_results",
	"conversations",
	"messages",
	"vulnerabilities",
	"assets",
	"projects",
	"xss_payloads",
	"xss_captures",
	"c2_listeners",
	"c2_sessions",
	"c2_tasks",
	"webshell_connections",
	"security_ops_runs",
	"batch_tasks",
	"workflow_runs",
	"knowledge_base_items",
}

var loanFeatureTables = []string{
	"loan_cases",
	"loan_applications",
	"loan_amount_sources",
	"loan_contract_details",
	"loan_repay_plans",
	"loan_table_manifest",
}

var knowledgeFeatureTables = []string{
	"knowledge_base_items",
	"knowledge_embeddings",
	"knowledge_retrieval_logs",
}

var recordsFeatureTables = []string{
	"record_types",
	"records",
}
var assetIntelFeatureTables = []string{
	"assets",
	"snapshots",
	"query_history",
}

// Catalog 回傳本機資料庫與新增功能（跳轉驗證、貸款主檔等）的狀態，不含列內容。
func (h *DatabasesHandler) Catalog(c *gin.Context) {
	wd, _ := os.Getwd()
	mainPath := resolveDataPath(h.cfgPath("database"), wd)
	knowledgePath := resolveDataPath(h.cfgPath("knowledge"), wd)
	loanPath := ""
	if h.loan != nil {
		loanPath = resolveDataPath(h.loan.DBPath(), wd)
	}
	assetPath := ""
	if h.assetIntel != nil {
		assetPath = resolveDataPath(h.assetIntel.DBPath(), wd)
	}
	recordsPath := ""
	if h.records != nil {
		recordsPath = resolveDataPath(h.records.DBPath(), wd)
	}
	records := inspectSQLite("records", "提取记录库", "扫描器提取的资料（贷款／订单／帐号／个资），自动去重", recordsPath, "records", recordsFeatureTables)

	main := inspectSQLite("platform", "平台主库", "会话、漏洞、批次跳转验证、XSS、C2、WebShell、扫描任务", mainPath, "redirect-verify", platformFeatureTables)
	knowledge := inspectSQLite("knowledge", "知识库", "知识项与向量嵌入", knowledgePath, "knowledge-management", knowledgeFeatureTables)
	loan := inspectSQLite("loan", "贷款案件主档", "中租 mid-sign 案件主档 v5（只读）", loanPath, "loan-cases", loanFeatureTables)
	asset := inspectSQLite("asset_intel", "资产情报库", "FOFA / ZoomEye 资产情报缓存", assetPath, "asset-intel", assetIntelFeatureTables)

	redirect := gin.H{}
	if h.cfg != nil {
		endpoints := append([]string(nil), h.cfg.Redirect.URLs...)
		redirect = gin.H{
			"id":          "redirect_verify",
			"name":        "批次跳转验证",
			"page":        "redirect-verify",
			"enabled":     h.cfg.Redirect.EnabledEffective(),
			"attach_scan": h.cfg.Redirect.AttachScanEffective(),
			"endpoints":   endpoints,
			"tables":      []string{"redirect_verify_runs", "redirect_verify_results"},
			"counts": gin.H{
				"runs":    tableCount(main.tables, "redirect_verify_runs"),
				"results": tableCount(main.tables, "redirect_verify_results"),
			},
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"ok": true,
		"databases": []gin.H{
			main.JSON(),
			knowledge.JSON(),
			loan.JSON(),
			asset.JSON(),
			records.JSON(),
		},
		"features": []gin.H{
			redirect,
			{
				"id":       "loan_cases",
				"name":     "贷款案件主档",
				"page":     "loan-cases",
				"imported": loan.Exists,
				"path":     loan.Path,
				"tables":   loanFeatureTables,
				"counts":   loan.Tables,
			},
			{
				"id":       "records",
				"name":     "提取记录主控台",
				"page":     "records",
				"imported": records.Exists,
				"path":     records.Path,
				"tables":   recordsFeatureTables,
				"counts":   records.Tables,
			},
			{
				"id":     "xss",
				"name":   "XSS 收割",
				"page":   "xss",
				"tables": []string{"xss_payloads", "xss_captures"},
				"counts": gin.H{
					"payloads": tableCount(main.tables, "xss_payloads"),
					"captures": tableCount(main.tables, "xss_captures"),
				},
			},
			{
				"id":     "c2",
				"name":   "C2",
				"page":   "c2-sessions",
				"tables": []string{"c2_listeners", "c2_sessions", "c2_tasks"},
				"counts": gin.H{
					"listeners": tableCount(main.tables, "c2_listeners"),
					"sessions":  tableCount(main.tables, "c2_sessions"),
					"tasks":     tableCount(main.tables, "c2_tasks"),
				},
			},
			{
				"id":     "security_ops",
				"name":   "Web 安全扫描",
				"page":   "security-ops",
				"tables": []string{"security_ops_runs"},
				"counts": gin.H{"runs": tableCount(main.tables, "security_ops_runs")},
			},
			{
				"id":     "webshell",
				"name":   "WebShell",
				"page":   "webshell",
				"tables": []string{"webshell_connections"},
				"counts": gin.H{"connections": tableCount(main.tables, "webshell_connections")},
			},
		},
	})
}

func (h *DatabasesHandler) cfgPath(kind string) string {
	if h == nil || h.cfg == nil {
		return ""
	}
	switch kind {
	case "database":
		p := h.cfg.Database.Path
		if p == "" {
			return "data/conversations.db"
		}
		return p
	case "knowledge":
		return h.cfg.Database.KnowledgeDBPath
	}
	return ""
}

func resolveDataPath(p, wd string) string {
	if p == "" {
		return ""
	}
	if filepath.IsAbs(p) {
		return p
	}
	if wd == "" {
		return p
	}
	return filepath.Join(wd, p)
}

type sqliteInspect struct {
	ID         string
	Name       string
	Role       string
	Path       string
	Exists     bool
	SizeBytes  int64
	ModifiedAt string
	TableCount int
	Tables     map[string]int64
	Page       string
	Error      string
	tables     map[string]int64
}

func (s sqliteInspect) JSON() gin.H {
	out := gin.H{
		"id":          s.ID,
		"name":        s.Name,
		"role":        s.Role,
		"path":        s.Path,
		"exists":      s.Exists,
		"size_bytes":  s.SizeBytes,
		"modified_at": s.ModifiedAt,
		"table_count": s.TableCount,
		"tables":      s.Tables,
		"page":        s.Page,
	}
	if s.Error != "" {
		out["error"] = s.Error
	}
	return out
}

func inspectSQLite(id, name, role, path, page string, interesting []string) sqliteInspect {
	out := sqliteInspect{
		ID:     id,
		Name:   name,
		Role:   role,
		Path:   path,
		Page:   page,
		Tables: map[string]int64{},
		tables: map[string]int64{},
	}
	if path == "" {
		return out
	}
	info, err := os.Stat(path)
	if err != nil {
		if !os.IsNotExist(err) {
			out.Error = err.Error()
		}
		return out
	}
	out.Exists = true
	out.SizeBytes = info.Size()
	out.ModifiedAt = info.ModTime().UTC().Format(time.RFC3339)

	db, err := openSQLiteRO(path)
	if err != nil {
		out.Error = err.Error()
		return out
	}
	if db == nil {
		return out
	}
	defer db.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 4*time.Second)
	defer cancel()
	var n int
	if err := db.QueryRowContext(ctx, `SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'`).Scan(&n); err == nil {
		out.TableCount = n
	}
	for _, table := range interesting {
		count, ok := countTable(ctx, db, table)
		if !ok {
			continue
		}
		out.Tables[table] = count
		out.tables[table] = count
	}
	return out
}

func countTable(ctx context.Context, db *sql.DB, table string) (int64, bool) {
	var n int64
	err := db.QueryRowContext(ctx, "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", table).Scan(&n)
	if err != nil || n == 0 {
		return 0, false
	}
	quoted := `"` + strings.ReplaceAll(table, `"`, ``) + `"`
	if err := db.QueryRowContext(ctx, "SELECT COUNT(*) FROM "+quoted).Scan(&n); err != nil {
		return 0, false
	}
	return n, true
}

func tableCount(m map[string]int64, name string) int64 {
	if m == nil {
		return 0
	}
	return m[name]
}
