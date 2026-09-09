package handler

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"

	"jysecai/internal/database"
	"jysecai/internal/security"
	"jysecai/internal/sentinel"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go.uber.org/zap"
)

type SentinelHandler struct {
	db          *database.DB
	logger      *zap.Logger
	activeScans map[string]*sentinel.ScanSnapshot
	activeMu    sync.RWMutex
}

func NewSentinelHandler(db *database.DB, logger *zap.Logger) *SentinelHandler {
	return &SentinelHandler{
		db:          db,
		logger:      logger,
		activeScans: make(map[string]*sentinel.ScanSnapshot),
	}
}

type ScanRequest struct {
	Target string `json:"target" binding:"required"`
}

// StartScanTarget 啟動背景非同步暴露面探測任務並返回初始快照
func (h *SentinelHandler) StartScanTarget(target string) (*sentinel.ScanSnapshot, error) {
	val := sentinel.ValidateTarget(target)
	if !val.OK {
		return nil, fmt.Errorf("%s", val.Error)
	}

	scanID := uuid.New().String()
	snapshot := &sentinel.ScanSnapshot{
		ID:         scanID,
		Target:     val.Target,
		TargetKind: val.Kind,
		CreatedAt:  time.Now(),
		Status:     "running",
	}

	h.activeMu.Lock()
	h.activeScans[scanID] = snapshot
	h.activeMu.Unlock()

	// 保存任務至 DB
	if err := h.db.SaveSentinelScan(snapshot); err != nil {
		h.logger.Warn("保存初始暴露面探測任務失敗", zap.Error(err))
	}

	// 背景異步執行探測任務
	go func(sid string, target string) {
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
		defer cancel()

		result, err := sentinel.RunScan(ctx, target)
		if err != nil {
			h.activeMu.Lock()
			if s, ok := h.activeScans[sid]; ok {
				s.Status = "failed"
				s.Error = err.Error()
				s.FinishedAt = time.Now().Format(time.RFC3339)
				_ = h.db.SaveSentinelScan(s)
			}
			h.activeMu.Unlock()
			h.logger.Error("暴露面探測失敗", zap.String("target", target), zap.Error(err))
			return
		}

		result.ID = sid
		h.activeMu.Lock()
		h.activeScans[sid] = result
		h.activeMu.Unlock()

		if saveErr := h.db.SaveSentinelScan(result); saveErr != nil {
			h.logger.Error("保存暴露面探測結果失敗", zap.String("target", target), zap.Error(saveErr))
		}
	}(scanID, val.Target)

	return snapshot, nil
}

// RunScanSync 同步執行暴露面探測直到完成或超時
func (h *SentinelHandler) RunScanSync(ctx context.Context, target string) (*sentinel.ScanSnapshot, error) {
	val := sentinel.ValidateTarget(target)
	if !val.OK {
		return nil, fmt.Errorf("%s", val.Error)
	}

	scanID := uuid.New().String()
	snapshot := &sentinel.ScanSnapshot{
		ID:         scanID,
		Target:     val.Target,
		TargetKind: val.Kind,
		CreatedAt:  time.Now(),
		Status:     "running",
	}

	h.activeMu.Lock()
	h.activeScans[scanID] = snapshot
	h.activeMu.Unlock()
	_ = h.db.SaveSentinelScan(snapshot)

	result, err := sentinel.RunScan(ctx, val.Target)
	if err != nil {
		h.activeMu.Lock()
		snapshot.Status = "failed"
		snapshot.Error = err.Error()
		snapshot.FinishedAt = time.Now().Format(time.RFC3339)
		_ = h.db.SaveSentinelScan(snapshot)
		h.activeMu.Unlock()
		return snapshot, err
	}

	result.ID = scanID
	h.activeMu.Lock()
	h.activeScans[scanID] = result
	h.activeMu.Unlock()
	_ = h.db.SaveSentinelScan(result)

	return result, nil
}

// StartScan 啟動暴露面探測任務（HTTP API）
func (h *SentinelHandler) StartScan(c *gin.Context) {
	var req ScanRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "請提供有效的 target (二級域名或公網 IPv4)"})
		return
	}

	snapshot, err := h.StartScanTarget(req.Target)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"scan_id": snapshot.ID,
		"target":  snapshot.Target,
		"status":  "running",
	})
}

// GetScanByID 查詢指定任務快照（先查記憶體中的活動任務，再查資料庫；若 id 為空則返回最新快照）
func (h *SentinelHandler) GetScanByID(scanID string) (*sentinel.ScanSnapshot, error) {
	scanID = strings.TrimSpace(scanID)
	if scanID == "" {
		return h.db.GetLatestSentinelScan()
	}
	h.activeMu.RLock()
	if s, ok := h.activeScans[scanID]; ok {
		h.activeMu.RUnlock()
		return s, nil
	}
	h.activeMu.RUnlock()
	return h.db.GetSentinelScanByID(scanID)
}

// GetLatestScanSnapshot 獲取最近一次探測快照
func (h *SentinelHandler) GetLatestScanSnapshot() (*sentinel.ScanSnapshot, error) {
	return h.db.GetLatestSentinelScan()
}

// GetScanStatus 查詢指定任務狀態（HTTP API）
func (h *SentinelHandler) GetScanStatus(c *gin.Context) {
	scanID := strings.TrimSpace(c.Param("id"))
	if scanID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "無效的任務 ID"})
		return
	}

	snapshot, err := h.GetScanByID(scanID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "查詢任務失敗: " + err.Error()})
		return
	}
	if snapshot == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "未找到該探測任務"})
		return
	}

	c.JSON(http.StatusOK, snapshot)
}

// GetLatestScan 獲取最近一次探測快照（HTTP API）
func (h *SentinelHandler) GetLatestScan(c *gin.Context) {
	snapshot, err := h.GetLatestScanSnapshot()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "獲取最新快照失敗: " + err.Error()})
		return
	}
	if snapshot == nil {
		c.JSON(http.StatusOK, gin.H{"snapshot": nil})
		return
	}
	c.JSON(http.StatusOK, snapshot)
}

// ListScans 獲取歷史探測記錄清單
func (h *SentinelHandler) ListScans(c *gin.Context) {
	records, err := h.db.ListSentinelScans(30)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "獲取歷史列表失敗: " + err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"scans": records})
}

type SyncAssetsRequest struct {
	ScanID    string `json:"scan_id" binding:"required"`
	ProjectID string `json:"project_id"`
}

// SyncAssetsDirect 將暴露面發現的主機與端口批量同步到系統資產庫
func (h *SentinelHandler) SyncAssetsDirect(scanID, projectID, userID string) (*database.AssetImportResult, int, error) {
	snapshot, err := h.GetScanByID(scanID)
	if err != nil {
		return nil, 0, err
	}
	if snapshot == nil {
		return nil, 0, fmt.Errorf("未找到對應的探測快照")
	}

	if userID == "" {
		userID = "admin"
	}

	var assetsToUpsert []*database.Asset
	now := time.Now()

	// 根據 Ports 與 Assets 生成資產對象
	for _, p := range snapshot.Ports {
		a := &database.Asset{
			ID:          uuid.New().String(),
			ProjectID:   strings.TrimSpace(projectID),
			Host:        p.Host,
			IP:          p.IP,
			Port:        p.Port,
			Protocol:    strings.ToLower(p.Service),
			Server:      p.Service,
			Source:      "sentinel",
			SourceQuery: snapshot.Target,
			Status:      "active",
			Tags:        []string{"sentinel", "surface-watch"},
			FirstSeenAt: now,
			LastSeenAt:  now,
			CreatedAt:   now,
			UpdatedAt:   now,
		}
		if p.IP != p.Host {
			a.Domain = p.Host
		}
		// 根據端點補齊標題
		for _, ep := range snapshot.Endpoints {
			if strings.Contains(ep.URL, p.Host) && ep.Title != "" {
				a.Title = ep.Title
				break
			}
		}
		assetsToUpsert = append(assetsToUpsert, a)
	}

	// 如果沒有開放端口但有主機在線，至少寫入一條記錄 (port=0)
	if len(assetsToUpsert) == 0 {
		for _, item := range snapshot.Assets {
			if item.Alive {
				a := &database.Asset{
					ID:          uuid.New().String(),
					ProjectID:   strings.TrimSpace(projectID),
					Host:        item.Host,
					IP:          item.IP,
					Port:        0,
					Domain:      item.Host,
					Source:      "sentinel",
					SourceQuery: snapshot.Target,
					Status:      "active",
					Tags:        []string{"sentinel", item.Scope},
					Title:       item.Title,
					FirstSeenAt: now,
					LastSeenAt:  now,
					CreatedAt:   now,
					UpdatedAt:   now,
				}
				assetsToUpsert = append(assetsToUpsert, a)
			}
		}
	}

	result, err := h.db.UpsertAssets(assetsToUpsert, userID, true)
	if err != nil {
		return nil, len(assetsToUpsert), err
	}

	return &result, len(assetsToUpsert), nil
}

// SyncToAssets 將暴露面發現的主機與端口批量同步到系統資產庫（HTTP API）
func (h *SentinelHandler) SyncToAssets(c *gin.Context) {
	var req SyncAssetsRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "請指定 scan_id"})
		return
	}

	userID := "admin"
	if session, ok := security.CurrentSession(c); ok && session.UserID != "" {
		userID = session.UserID
		if session.Scope != database.RBACScopeAll && strings.TrimSpace(req.ProjectID) != "" {
			if !h.db.UserCanAccessResource(session.UserID, session.Scope, "project", strings.TrimSpace(req.ProjectID)) {
				c.JSON(http.StatusForbidden, gin.H{"error": "无权访问该项目"})
				return
			}
		}
	}

	result, total, err := h.SyncAssetsDirect(req.ScanID, req.ProjectID, userID)
	if err != nil {
		if strings.Contains(err.Error(), "未找到") {
			c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "同步資產庫失敗: " + err.Error()})
		}
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"created": result.Created,
		"updated": result.Updated,
		"skipped": result.Skipped,
		"total":   total,
	})
}

type SyncVulnsRequest struct {
	ScanID    string `json:"scan_id" binding:"required"`
	ProjectID string `json:"project_id"`
}

// SyncVulnsDirect 將高危/中危發現項同步到系統漏洞庫
func (h *SentinelHandler) SyncVulnsDirect(scanID, projectID string) (int, int, error) {
	snapshot, err := h.GetScanByID(scanID)
	if err != nil {
		return 0, 0, err
	}
	if snapshot == nil {
		return 0, 0, fmt.Errorf("未找到對應的探測快照")
	}

	createdCount := 0
	skippedCount := 0
	now := time.Now()

	// 篩選 High 與 Medium 級別的發現項
	for _, f := range snapshot.Findings {
		if f.Severity != "high" && f.Severity != "medium" {
			continue
		}

		target := f.Host
		if f.URL != "" {
			target = f.URL
		}

		// 去重檢查：若相同 Target 和 Title 的漏洞已存在則跳過
		if existing, _ := h.db.FindVulnerabilityByTargetAndTitle(projectID, target, f.Title); existing != nil {
			skippedCount++
			continue
		}

		vuln := &database.Vulnerability{
			ID:          uuid.New().String(),
			ProjectID:   strings.TrimSpace(projectID),
			Title:       f.Title,
			Description: f.Detail,
			Severity:    f.Severity,
			Type:        f.Category,
			Target:      target,
			Evidence:    f.Detail,
			Status:      "open",
			TaskTag:     "sentinel-scan",
			CreatedAt:   now,
			UpdatedAt:   now,
		}

		if _, err := h.db.CreateVulnerability(vuln); err == nil {
			createdCount++
		} else {
			h.logger.Warn("寫入漏洞記錄失敗", zap.Error(err))
		}
	}

	return createdCount, skippedCount, nil
}

// SyncToVulnerabilities 將高危/中危發現項同步到系統漏洞庫（HTTP API）
func (h *SentinelHandler) SyncToVulnerabilities(c *gin.Context) {
	var req SyncVulnsRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "請指定 scan_id"})
		return
	}

	if session, ok := security.CurrentSession(c); ok && session.Scope != database.RBACScopeAll && strings.TrimSpace(req.ProjectID) != "" {
		if !h.db.UserCanAccessResource(session.UserID, session.Scope, "project", strings.TrimSpace(req.ProjectID)) {
			c.JSON(http.StatusForbidden, gin.H{"error": "无权访问该项目"})
			return
		}
	}

	createdCount, skippedCount, err := h.SyncVulnsDirect(req.ScanID, req.ProjectID)
	if err != nil {
		if strings.Contains(err.Error(), "未找到") {
			c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		}
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"created": createdCount,
		"skipped": skippedCount,
	})
}
