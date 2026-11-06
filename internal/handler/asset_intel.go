package handler

import (
	"net/http"
	"os"
	"strings"
	"time"

	"context"

	"jysecai/internal/config"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// AssetIntelHandler 提供 JySecAI 既有 Web 與 asset_intelligence MCP 的只讀橋接。
//
// 設計原則:
//   - 不修改既有 fofa.go 路由, 獨立 /api/assets-intel/* 命名空間
//   - 不直接呼叫外部 API (金鑰由環境變數或 config 注入, 前端不暴露)
//   - 讀取 asset_intelligence MCP 的 SQLite 資料庫 (WAL 可併行讀)
//   - 回傳前遮蔽敏感欄位 (api_key / token / password 等)
type AssetIntelHandler struct {
	cfg    *config.Config
	logger *zap.Logger
	dbPath string
}

// NewAssetIntelHandler 建立 handler. dbPath 預設讀 ASSET_INTEL_DB_PATH 環境變數.
func NewAssetIntelHandler(cfg *config.Config, logger *zap.Logger) *AssetIntelHandler {
	dbPath := os.Getenv("ASSET_INTEL_DB_PATH")
	if dbPath == "" {
		home, _ := os.UserHomeDir()
		if home == "" {
			dbPath = "data/jysecai-assets/assets.db"
		} else {
			dbPath = home + "/AppData/Local/JySecAI/assets/assets.db"
		}
	}
	return &AssetIntelHandler{cfg: cfg, logger: logger, dbPath: dbPath}
}

// dbStats 從資料庫讀取統計資訊.
type dbStats struct {
	TotalAssets    int            `json:"total_assets"`
	UniqueIPs      int            `json:"unique_ips"`
	UniqueDomains  int            `json:"unique_domains"`
	ByProvider     map[string]int `json:"by_provider"`
	ByService      map[string]int `json:"by_service"`
	Recent24h      int            `json:"recent_24h"`
	LastUpdated    string         `json:"last_updated"`
	Snapshots      int            `json:"snapshots"`
	QueryHistoryRows int          `json:"query_history_rows"`
}

func (h *AssetIntelHandler) loadStats() (dbStats, error) {
	stats := dbStats{
		ByProvider: map[string]int{},
		ByService:  map[string]int{},
	}
	if h.dbPath == "" {
		return stats, nil
	}
	db, err := openSQLiteRO(h.dbPath)
	if db == nil {
		if err != nil {
			return stats, err
		}
		return stats, nil
	}
	defer db.Close()

	ctx := context.Background()
	_ = db.QueryRowContext(ctx, "SELECT COUNT(*) FROM assets").Scan(&stats.TotalAssets)
	_ = db.QueryRowContext(ctx, "SELECT COUNT(DISTINCT ip) FROM assets WHERE ip != ''").Scan(&stats.UniqueIPs)
	_ = db.QueryRowContext(ctx, "SELECT COUNT(DISTINCT domain) FROM assets WHERE domain != ''").Scan(&stats.UniqueDomains)
	cutoff := time.Now().Add(-24 * time.Hour).Format(time.RFC3339)
	_ = db.QueryRowContext(ctx, "SELECT COUNT(*) FROM assets WHERE observed_at > ?", cutoff).Scan(&stats.Recent24h)
	_ = db.QueryRowContext(ctx, "SELECT MAX(observed_at) FROM assets").Scan(&stats.LastUpdated)
	_ = db.QueryRowContext(ctx, "SELECT COUNT(*) FROM snapshots").Scan(&stats.Snapshots)
	_ = db.QueryRowContext(ctx, "SELECT COUNT(*) FROM query_history").Scan(&stats.QueryHistoryRows)

	// by_service top 50
	if rows, err := db.QueryContext(ctx,
		"SELECT service, COUNT(*) FROM assets WHERE service != '' GROUP BY service ORDER BY COUNT(*) DESC LIMIT 50"); err == nil {
		defer rows.Close()
		for rows.Next() {
			var svc string
			var cnt int
			if err := rows.Scan(&svc, &cnt); err == nil {
				stats.ByService[svc] = cnt
			}
		}
	}
	return stats, nil
}

// List 回傳統計與配置狀態 (唯讀, 不呼叫外部 API).
func (h *AssetIntelHandler) List(c *gin.Context) {
	stats, _ := h.loadStats()
	fofaConfigured := h.cfg != nil && (h.cfg.FOFA.APIKey != "" || hasEnv("FOFA_API_KEY"))
	zoomeyeConfigured := h.cfg != nil && (h.cfg.ZoomEye.APIKey != "" || hasEnv("ZOOMEYE_API_KEY"))
	c.JSON(http.StatusOK, gin.H{
		"provider":    "asset_intel",
		"db_path":     h.dbPath,
		"db_exists":   fileExists(h.dbPath),
		"stats":       stats,
		"scope_file":  os.Getenv("ASSET_INTEL_SCOPE_FILE"),
		"scope_exists": fileExists(os.Getenv("ASSET_INTEL_SCOPE_FILE")),
		"has_fofa":    fofaConfigured,
		"has_zoomeye": zoomeyeConfigured,
	})
}

// RecentHistory 回傳最近 N 筆查詢歷史 (唯讀).
func (h *AssetIntelHandler) RecentHistory(c *gin.Context) {
	limit := queryInt(c, "limit", 30)
	if limit < 1 || limit > 200 {
		limit = 30
	}
	if h.dbPath == "" || !fileExists(h.dbPath) {
		c.JSON(http.StatusOK, gin.H{"items": []gin.H{}, "count": 0})
		return
	}
	db, _ := openSQLiteRO(h.dbPath)
	if db == nil {
		c.JSON(http.StatusOK, gin.H{"items": []gin.H{}, "count": 0})
		return
	}
	defer db.Close()

	rows, err := db.QueryContext(context.Background(),
		"SELECT trace_id, provider, query, page, ok, error_code, total, results_count, api_calls, credits_used, duration_ms, scope_id, created_at FROM query_history ORDER BY id DESC LIMIT ?", limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	items := make([]gin.H, 0, limit)
	for rows.Next() {
		var (
			traceID, provider, query, errCode, scopeID, createdAt string
			page, ok, total, resultsCount, apiCalls, credits, duration int
		)
		if err := rows.Scan(&traceID, &provider, &query, &page, &ok, &errCode, &total, &resultsCount, &apiCalls, &credits, &duration, &scopeID, &createdAt); err != nil {
			continue
		}
		items = append(items, gin.H{
			"trace_id":      traceID,
			"provider":      provider,
			"query":         sanitizeQuery(query),
			"page":          page,
			"ok":            ok == 1,
			"error_code":    errCode,
			"total":         total,
			"results_count": resultsCount,
			"api_calls":     apiCalls,
			"credits_used":  credits,
			"duration_ms":   duration,
			"scope_id":      scopeID,
			"created_at":    createdAt,
		})
	}
	c.JSON(http.StatusOK, gin.H{"items": items, "count": len(items)})
}

// ProviderStatus 回傳 provider 金鑰設定狀態 (不洩漏金鑰本身).
func (h *AssetIntelHandler) ProviderStatus(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"fofa":    gin.H{"configured": hasEnv("FOFA_API_KEY") || (h.cfg != nil && h.cfg.FOFA.APIKey != "")},
		"zoomeye": gin.H{"configured": hasEnv("ZOOMEYE_API_KEY") || (h.cfg != nil && h.cfg.ZoomEye.APIKey != "")},
		"scope":   gin.H{"file": os.Getenv("ASSET_INTEL_SCOPE_FILE"), "exists": fileExists(os.Getenv("ASSET_INTEL_SCOPE_FILE"))},
		"db":      gin.H{"path": h.dbPath, "exists": fileExists(h.dbPath)},
	})
}

// Search 執行授權範圍內的資產搜尋 (唯讀, 不直接呼叫外部 API).
// 從 asset_intelligence MCP 的 SQLite 資料庫回傳已儲存的資產, 支援 ip / domain / service 過濾.
func (h *AssetIntelHandler) Search(c *gin.Context) {
	ip := strings.TrimSpace(c.Query("ip"))
	domain := strings.TrimSpace(c.Query("domain"))
	service := strings.TrimSpace(c.Query("service"))
	limit := queryInt(c, "limit", 100)
	if limit < 1 || limit > 1000 {
		limit = 100
	}
	if h.dbPath == "" || !fileExists(h.dbPath) {
		c.JSON(http.StatusOK, gin.H{"items": []gin.H{}, "count": 0, "db_exists": false})
		return
	}
	db, _ := openSQLiteRO(h.dbPath)
	if db == nil {
		c.JSON(http.StatusOK, gin.H{"items": []gin.H{}, "count": 0, "db_exists": false})
		return
	}
	defer db.Close()

	// 動態建構 WHERE 子句 (僅使用參數綁定, 防 SQL 注入)
	where := "WHERE 1=1"
	args := make([]any, 0, 4)
	if ip != "" {
		where += " AND ip = ?"
		args = append(args, ip)
	}
	if domain != "" {
		where += " AND (domain = ? OR hostname = ?)"
		args = append(args, domain, domain)
	}
	if service != "" {
		where += " AND service = ?"
		args = append(args, service)
	}
	args = append(args, limit)

	rows, err := db.QueryContext(context.Background(),
		`SELECT asset_id, ip, domain, hostname, port, protocol, service, product, version,
		        banner, title, country, city, source_providers, first_seen, last_seen,
		        observed_at, confidence, authorization_scope_id
		 FROM assets `+where+` ORDER BY observed_at DESC LIMIT ?`,
		args...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	items := make([]gin.H, 0, limit)
	for rows.Next() {
		var (
			assetID, ipVal, domainVal, hostVal, protocol, serviceVal, product, version, banner, title, country, city, providers, firstSeen, lastSeen, observedAt, scopeID string
			port, confidenceVal int
		)
		if err := rows.Scan(&assetID, &ipVal, &domainVal, &hostVal, &port, &protocol, &serviceVal, &product, &version, &banner, &title, &country, &city, &providers, &firstSeen, &lastSeen, &observedAt, &confidenceVal, &scopeID); err != nil {
			continue
		}
		// 遮蔽 banner 中的潛在敏感欄位
		if len(banner) > 512 {
			banner = banner[:512] + "..."
		}
		items = append(items, gin.H{
			"asset_id":        assetID,
			"ip":              ipVal,
			"domain":          domainVal,
			"hostname":        hostVal,
			"port":            port,
			"protocol":        protocol,
			"service":         serviceVal,
			"product":         product,
			"version":         version,
			"banner":          banner,
			"title":           title,
			"country":         country,
			"city":            city,
			"source_providers": providers,
			"confidence":      confidenceVal,
			"first_seen":      firstSeen,
			"last_seen":       lastSeen,
			"observed_at":     observedAt,
			"scope_id":        scopeID,
		})
	}
	c.JSON(http.StatusOK, gin.H{"items": items, "count": len(items), "db_exists": true})
}

// Quota 回傳每日額度使用統計 (唯讀).
func (h *AssetIntelHandler) Quota(c *gin.Context) {
	if h.dbPath == "" || !fileExists(h.dbPath) {
		c.JSON(http.StatusOK, gin.H{"by_day": map[string]gin.H{}, "today": gin.H{}})
		return
	}
	db, _ := openSQLiteRO(h.dbPath)
	if db == nil {
		c.JSON(http.StatusOK, gin.H{"by_day": map[string]gin.H{}, "today": gin.H{}})
		return
	}
	defer db.Close()

	today := time.Now().UTC().Format("2006-01-02")
	byDay := map[string]gin.H{}
	todayStats := gin.H{"requests": 0, "credits": 0}

	rows, err := db.QueryContext(context.Background(),
		"SELECT day, provider, SUM(requests), SUM(credits) FROM quota_usage WHERE day >= date('now', '-7 days') GROUP BY day, provider ORDER BY day DESC")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	for rows.Next() {
		var day, provider string
		var requests, credits int
		if err := rows.Scan(&day, &provider, &requests, &credits); err != nil {
			continue
		}
		dayEntry := byDay[day]
		if dayEntry == nil {
			dayEntry = gin.H{"requests": 0, "credits": 0, "by_provider": map[string]gin.H{}}
		}
		dayEntry["requests"] = dayEntry["requests"].(int) + requests
		dayEntry["credits"] = dayEntry["credits"].(int) + credits
		if bp, ok := dayEntry["by_provider"].(map[string]gin.H); ok {
			bp[provider] = gin.H{"requests": requests, "credits": credits}
		}
		byDay[day] = dayEntry
		if day == today {
			todayStats["requests"] = todayStats["requests"].(int) + requests
			todayStats["credits"] = todayStats["credits"].(int) + credits
		}
	}
	c.JSON(http.StatusOK, gin.H{"by_day": byDay, "today": todayStats, "today_date": today})
}

// Snapshots 回傳快照列表 (唯讀).
func (h *AssetIntelHandler) Snapshots(c *gin.Context) {
	limit := queryInt(c, "limit", 20)
	if limit < 1 || limit > 100 {
		limit = 20
	}
	if h.dbPath == "" || !fileExists(h.dbPath) {
		c.JSON(http.StatusOK, gin.H{"items": []gin.H{}, "count": 0})
		return
	}
	db, _ := openSQLiteRO(h.dbPath)
	if db == nil {
		c.JSON(http.StatusOK, gin.H{"items": []gin.H{}, "count": 0})
		return
	}
	defer db.Close()

	rows, err := db.QueryContext(context.Background(),
		"SELECT id, scope_id, label, asset_count, created_at, substr(payload, 1, 200) FROM snapshots ORDER BY id DESC LIMIT ?", limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	items := make([]gin.H, 0, limit)
	for rows.Next() {
		var (
			id, scopeID, label string
			assetCount         int
			createdAt          string
			payloadPreview string
		)
		if err := rows.Scan(&id, &scopeID, &label, &assetCount, &createdAt, &payloadPreview); err != nil {
			continue
		}
		items = append(items, gin.H{
			"id":             id,
			"scope_id":       scopeID,
			"label":          label,
			"asset_count":    assetCount,
			"created_at":     createdAt,
			"payload_preview": payloadPreview,
		})
	}
	c.JSON(http.StatusOK, gin.H{"items": items, "count": len(items)})
}

// ---- helpers ----

func fileExists(p string) bool {
	if p == "" {
		return false
	}
	_, err := os.Stat(p)
	return err == nil
}

func hasEnv(k string) bool {
	return strings.TrimSpace(os.Getenv(k)) != ""
}

func queryInt(c *gin.Context, key string, def int) int {
	v := c.Query(key)
	if v == "" {
		return def
	}
	n := 0
	for _, ch := range v {
		if ch < '0' || ch > '9' {
			return def
		}
		n = n*10 + int(ch-'0')
	}
	return n
}

func sanitizeQuery(q string) string {
	q = strings.TrimSpace(q)
	if len(q) > 200 {
		q = q[:200] + "..."
	}
	return q
}
