package handler

import (
	"context"
	"encoding/csv"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"

	"jysecai/internal/records"
	"jysecai/internal/security"
)

// RecordsHandler 提供「通用提取記錄」的管理主控台 API。
//
// 這一組端點是貸款案件主檔的泛化：型別（貸款案件／快遞訂單／帳號憑證／
// 資產指紋／風險漏洞／聯絡資料）由資料庫裡的型別定義決定，前端照定義排欄，
// 所以新增一種資料型別不需要改前端。
//
// 權限：讀取用 records:read，寫入（入庫）用 records:write，匯出用 records:export。
// 匯出與檢視刻意分開 —— 能看列表不等於能把整包資料帶走。
type RecordsHandler struct {
	logger *zap.Logger
	dbPath string
	store  *records.Store

	// 欄位有值率的快取。
	//
	// 為什麼要快取：ColumnFill 要逐列解析 fields_json，13 個型別合計 7 萬多列，
	// 每次 /api/records/types 都重算要 1~3 秒 —— 主控台一開就會卡住。
	// 這份資料只有入庫時才會變，所以快取 5 分鐘；入庫後主動失效。
	fillMu    sync.Mutex
	fillCache map[string]map[string]int64
	fillAt    time.Time
}

const fillCacheTTL = 5 * time.Minute

// NewRecordsHandler 建立 handler。dbPath 優先讀 RECORDS_DB_PATH。
func NewRecordsHandler(logger *zap.Logger) *RecordsHandler {
	h := &RecordsHandler{logger: logger, dbPath: resolveRecordsDBPath()}
	if store, err := records.Open(h.dbPath); err == nil {
		h.store = store
	} else if logger != nil {
		logger.Warn("records: 無法開啟提取記錄庫", zap.String("path", h.dbPath), zap.Error(err))
	}
	return h
}

func resolveRecordsDBPath() string {
	if p := strings.TrimSpace(os.Getenv("RECORDS_DB_PATH")); p != "" {
		return p
	}
	for _, p := range []string{
		"data/extracted_records.db",
		"/var/lib/jysecai/core/extracted_records.db",
		"/opt/jysecai/core/current/data/extracted_records.db",
	} {
		if fileExists(p) {
			return p
		}
	}
	return "data/extracted_records.db"
}

// DBPath 回傳儲存路徑。
func (h *RecordsHandler) DBPath() string {
	if h == nil {
		return ""
	}
	return h.dbPath
}

func (h *RecordsHandler) ready(c *gin.Context) bool {
	if h == nil || h.store == nil {
		c.JSON(http.StatusOK, gin.H{
			"ok": false, "db_missing": true, "db_path": h.DBPath(),
			"message": "提取記錄庫尚未建立（執行 cmd/records-ingest 匯入第一批資料後會自動建立）",
		})
		return false
	}
	return true
}

func recordsCtx(c *gin.Context) (context.Context, context.CancelFunc) {
	return context.WithTimeout(c.Request.Context(), 30*time.Second)
}

// RecordsTypes 回傳所有型別定義與筆數，供主控台生成分類頁籤。
func (h *RecordsHandler) RecordsTypes(c *gin.Context) {
	if !h.ready(c) {
		return
	}
	ctx, cancel := recordsCtx(c)
	defer cancel()
	defs, counts, err := h.store.Types(ctx)
	if err != nil {
		writeSecurityOpsError(c, http.StatusInternalServerError, "list_failed", "无法读取记录型别: "+err.Error())
		return
	}
	datasets, _ := h.store.Datasets(ctx)
	out := make([]gin.H, 0, len(defs))
	fills := h.columnFills(ctx, defs, counts)
	for _, def := range defs {
		// 欄位有值率：讓前端能把「這個欄位有多少筆真的有值」直接標出來，
		// 並預設只顯示有值的欄位（資料稀疏的型別不會半屏空白）。
		fill := fills[def.ID]
		out = append(out, gin.H{
			"id":            def.ID,
			"label":         def.Label,
			"description":   def.Description,
			"icon":          def.Icon,
			"columns":       def.Columns,
			"dedupe_fields": def.DedupeFields,
			"facet_column":  def.FacetColumn,
			"count":         counts[def.ID],
			"has_data":      counts[def.ID] > 0,
			"fill":          fill,
		})
	}
	c.JSON(http.StatusOK, gin.H{
		"ok": true, "types": out, "datasets": datasets,
		"db_path": h.DBPath(), "total": sumCounts(counts),
	})
}

func sumCounts(m map[string]int64) int64 {
	var total int64
	for _, n := range m {
		total += n
	}
	return total
}

// columnFills 取得各型別的欄位有值率，5 分鐘內重用同一份結果。
func (h *RecordsHandler) columnFills(ctx context.Context, defs []records.TypeDef,
	counts map[string]int64) map[string]map[string]int64 {
	h.fillMu.Lock()
	defer h.fillMu.Unlock()
	if h.fillCache == nil {
		h.fillCache = map[string]map[string]int64{}
	}
	if time.Since(h.fillAt) > fillCacheTTL {
		h.fillCache = map[string]map[string]int64{}
		h.fillAt = time.Now()
	}
	out := map[string]map[string]int64{}
	for _, def := range defs {
		if counts[def.ID] <= 0 {
			out[def.ID] = map[string]int64{}
			continue
		}
		if f, ok := h.fillCache[def.ID]; ok {
			out[def.ID] = f
			continue
		}
		f, err := h.store.ColumnFill(ctx, def.ID)
		if err != nil {
			f = map[string]int64{}
		}
		h.fillCache[def.ID] = f
		out[def.ID] = f
	}
	return out
}

// invalidateFillCache 在入庫後呼叫：有新資料進來，有值率要重算。
func (h *RecordsHandler) invalidateFillCache() {
	h.fillMu.Lock()
	h.fillCache = nil
	h.fillAt = time.Time{}
	h.fillMu.Unlock()
}

// RecordsList 分頁查詢記錄。
func (h *RecordsHandler) RecordsList(c *gin.Context) {
	if !h.ready(c) {
		return
	}
	ctx, cancel := recordsCtx(c)
	defer cancel()
	q := records.ListQuery{
		TypeID:   strings.TrimSpace(c.Query("type")),
		Dataset:  strings.TrimSpace(c.Query("dataset")),
		Query:    strings.TrimSpace(c.Query("q")),
		Page:     atoiDefault(c.Query("page"), 1),
		PageSize: atoiDefault(c.Query("page_size"), 50),
		SortBy:   strings.TrimSpace(c.Query("sort_by")),
		SortDir:  strings.TrimSpace(c.Query("sort_dir")),
	}
	page, err := h.store.List(ctx, q)
	if err != nil {
		writeSecurityOpsError(c, http.StatusInternalServerError, "list_failed", "无法读取记录: "+err.Error())
		return
	}
	facets := []records.FacetBucket{}
	if q.TypeID != "" {
		column := strings.TrimSpace(c.Query("facet"))
		if column == "" && page.Type != nil {
			column = page.Type.FacetColumn
		}
		if column != "" {
			facets, _ = h.store.Facet(ctx, q.TypeID, column)
		}
	}
	c.JSON(http.StatusOK, gin.H{
		"ok": true, "items": page.Items, "total": page.Total,
		"page": page.Page, "page_size": page.PageSize, "type": page.Type,
		"facet": facets, "facet_column": c.Query("facet"),
	})
}

// RecordsClassification 回傳某型別的分類統計。
func (h *RecordsHandler) RecordsClassification(c *gin.Context) {
	if !h.ready(c) {
		return
	}
	ctx, cancel := recordsCtx(c)
	defer cancel()
	typeID := strings.TrimSpace(c.Query("type"))
	column := strings.TrimSpace(c.Query("facet"))
	if column == "" {
		def, err := h.store.TypeDefOf(ctx, typeID)
		if err == nil && def != nil {
			column = def.FacetColumn
		}
	}
	buckets, err := h.store.Facet(ctx, typeID, column)
	if err != nil {
		writeSecurityOpsError(c, http.StatusInternalServerError, "list_failed", "无法读取分类统计: "+err.Error())
		return
	}
	c.JSON(http.StatusOK, gin.H{"ok": true, "type": typeID, "facet_column": column, "buckets": buckets})
}

// RecordsIngest 匯入一批記錄（自動去重）。
func (h *RecordsHandler) RecordsIngest(c *gin.Context) {
	if !h.ready(c) {
		return
	}
	var in records.IngestInput
	if err := c.ShouldBindJSON(&in); err != nil {
		writeSecurityOpsError(c, http.StatusBadRequest, "invalid_body", "无法解析汇入资料: "+err.Error())
		return
	}
	if strings.TrimSpace(in.TypeID) == "" {
		writeSecurityOpsError(c, http.StatusBadRequest, "invalid_body", "缺少 type_id")
		return
	}
	ctx, cancel := recordsCtx(c)
	defer cancel()
	res, err := h.store.Ingest(ctx, in)
	if err != nil {
		writeSecurityOpsError(c, http.StatusBadRequest, "ingest_failed", err.Error())
		return
	}
	h.invalidateFillCache()
	c.JSON(http.StatusOK, gin.H{
		"ok": true, "inserted": res.Inserted, "updated": res.Updated,
		"duplicate": res.Updated, "total": res.Total,
	})
}

// RecordsExport 匯出 CSV（欄位依型別定義排序）。
func (h *RecordsHandler) RecordsExport(c *gin.Context) {
	if !h.ready(c) {
		return
	}
	ctx, cancel := recordsCtx(c)
	defer cancel()
	q := records.ListQuery{
		TypeID:  strings.TrimSpace(c.Query("type")),
		Dataset: strings.TrimSpace(c.Query("dataset")),
		Query:   strings.TrimSpace(c.Query("q")),
	}
	rows, err := h.store.AllRows(ctx, q)
	if err != nil {
		writeSecurityOpsError(c, http.StatusInternalServerError, "export_failed", "无法读取记录: "+err.Error())
		return
	}
	var def *records.TypeDef
	if q.TypeID != "" {
		def, _ = h.store.TypeDefOf(ctx, q.TypeID)
	}
	header, body := records.FormatCSV(def, rows)

	name := "records"
	if def != nil {
		name = def.ID
	}
	if q.Dataset != "" {
		name += "_" + sanitizeFilePart(q.Dataset)
	}
	c.Header("Content-Type", "text/csv; charset=utf-8")
	c.Header("Content-Disposition", `attachment; filename="`+name+`.csv"`)
	c.Status(http.StatusOK)

	w := csv.NewWriter(c.Writer)
	_ = w.Write(header)
	for _, line := range body {
		_ = w.Write(line)
	}
	w.Flush()
}

func sanitizeFilePart(s string) string {
	var b strings.Builder
	for _, r := range strings.TrimSpace(s) {
		switch {
		case r >= 'a' && r <= 'z', r >= 'A' && r <= 'Z', r >= '0' && r <= '9', r == '-', r == '_':
			b.WriteRune(r)
		default:
			b.WriteRune('_')
		}
	}
	out := strings.Trim(b.String(), "_")
	if out == "" {
		return "dataset"
	}
	return out
}

func atoiDefault(s string, def int) int {
	s = strings.TrimSpace(s)
	if s == "" {
		return def
	}
	n, err := strconv.Atoi(s)
	if err != nil || n <= 0 {
		return def
	}
	return n
}

// RecordsDBPath 供 databases.go 的目錄頁使用。
func (h *RecordsHandler) RecordsDBPath() string {
	return h.DBPath()
}

// RecordsCount 回傳記錄總數（給目錄頁顯示）。
func (h *RecordsHandler) RecordsCount(ctx context.Context) int64 {
	if h == nil || h.store == nil {
		return 0
	}
	_, counts, err := h.store.Types(ctx)
	if err != nil {
		return 0
	}
	return sumCounts(counts)
}

// RecordsFeatureTables 是目錄頁要顯示的表名。
var RecordsFeatureTables = []string{"record_types", "records"}

// requireRecordsSession 供其他 handler 需要登入者時使用。
func requireRecordsSession(c *gin.Context) (security.Session, bool) {
	session, ok := security.CurrentSession(c)
	if !ok || session.UserID == "" {
		writeSecurityOpsError(c, http.StatusUnauthorized, "unauthorized", "需要登录")
		return security.Session{}, false
	}
	return session, true
}
