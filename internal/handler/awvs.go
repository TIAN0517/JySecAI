package handler

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"

	"jysecai/internal/database"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// AWVSHandler 處理 AWVS (Acunetix) 掃描器聯動
type AWVSHandler struct {
	db        *database.DB
	logger    *zap.Logger
	client    *http.Client
	mu        sync.RWMutex
	baseURL   string
	apiKey    string
}

// NewAWVSHandler 創建 AWVS 處理器
func NewAWVSHandler(db *database.DB, logger *zap.Logger, defaultURL, defaultAPIKey string) *AWVSHandler {
	apiURL := strings.TrimSpace(defaultURL)
	if apiURL == "" {
		apiURL = strings.TrimSpace(os.Getenv("JYSEC_AWVS_API_URL"))
	}
	if apiURL == "" {
		apiURL = strings.TrimSpace(os.Getenv("AWVS_API_URL"))
	}
	if apiURL == "" {
		apiURL = "https://localhost:3443"
	}

	apiKey := strings.TrimSpace(defaultAPIKey)
	if apiKey == "" {
		apiKey = strings.TrimSpace(os.Getenv("JYSEC_AWVS_API_KEY"))
	}
	if apiKey == "" {
		apiKey = strings.TrimSpace(os.Getenv("AWVS_API_KEY"))
	}

	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}
	client := &http.Client{
		Transport: tr,
		Timeout:   30 * time.Second,
	}

	return &AWVSHandler{
		db:      db,
		logger:  logger,
		client:  client,
		baseURL: strings.TrimRight(apiURL, "/"),
		apiKey:  apiKey,
	}
}

func (h *AWVSHandler) getBaseURL() string {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return h.baseURL
}

func (h *AWVSHandler) getAPIKey() string {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return h.apiKey
}

func (h *AWVSHandler) getEndpoint(path string) string {
	return fmt.Sprintf("%s/api/v1/%s", h.getBaseURL(), strings.TrimPrefix(path, "/"))
}

func (h *AWVSHandler) doRequest(method, path string, body io.Reader) (*http.Response, error) {
	fullURL := h.getEndpoint(path)
	req, err := http.NewRequest(method, fullURL, body)
	if err != nil {
		return nil, err
	}

	req.Header.Set("X-Auth", h.getAPIKey())
	req.Header.Set("Content-Type", "application/json")
	return h.client.Do(req)
}

// GetStatusInfo 獲取 AWVS 連線狀態與當前用戶資訊
func (h *AWVSHandler) GetStatusInfo() (map[string]interface{}, error) {
	baseURL := h.getBaseURL()
	if h.getAPIKey() == "" {
		return map[string]interface{}{
			"connected": false,
			"url":       baseURL,
			"error":     "AWVS API Key 未配置，請設置 JYSEC_AWVS_API_KEY 環境變數或在頁面配置",
		}, nil
	}
	resp, err := h.doRequest(http.MethodGet, "me", nil)
	if err != nil {
		return map[string]interface{}{
			"connected": false,
			"url":       baseURL,
			"error":     err.Error(),
		}, nil
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return map[string]interface{}{
			"connected":   false,
			"url":         baseURL,
			"status_code": resp.StatusCode,
			"error":       string(body),
		}, nil
	}

	var meData map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&meData); err != nil {
		return map[string]interface{}{
			"connected": false,
			"url":       baseURL,
			"error":     "解析 AWVS 回應失敗: " + err.Error(),
		}, nil
	}

	// 額外獲取 targets 數量
	targetCount := 0
	if targetsResp, err := h.doRequest(http.MethodGet, "targets", nil); err == nil {
		defer targetsResp.Body.Close()
		var targetsData struct {
			Pagination struct {
				Count int `json:"count"`
			} `json:"pagination"`
		}
		if err := json.NewDecoder(targetsResp.Body).Decode(&targetsData); err == nil {
			targetCount = targetsData.Pagination.Count
		}
	}

	return map[string]interface{}{
		"connected":    true,
		"url":          baseURL,
		"email":        meData["email"],
		"role":         meData["role"],
		"target_count": targetCount,
	}, nil
}

// GetStatus 獲取 AWVS 連線狀態與當前用戶資訊（HTTP API）
func (h *AWVSHandler) GetStatus(c *gin.Context) {
	info, _ := h.GetStatusInfo()
	c.JSON(http.StatusOK, info)
}

// ListTargetsInfo 列出 AWVS 所有目標
func (h *AWVSHandler) ListTargetsInfo() (map[string]interface{}, error) {
	resp, err := h.doRequest(http.MethodGet, "targets", nil)
	if err != nil {
		return nil, fmt.Errorf("請求 AWVS 失敗: %w", err)
	}
	defer resp.Body.Close()

	var data map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, fmt.Errorf("解析 targets 失敗: %w", err)
	}

	return data, nil
}

// ListTargets 列出 AWVS 所有目標（HTTP API）
func (h *AWVSHandler) ListTargets(c *gin.Context) {
	data, err := h.ListTargetsInfo()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, data)
}

// CreateTargetRequest 新增目標請求
type CreateTargetRequest struct {
	Address     string `json:"address" binding:"required"`
	Description string `json:"description"`
}

// CreateTarget 在 AWVS 中新增掃描目標
func (h *AWVSHandler) CreateTarget(c *gin.Context) {
	var req CreateTargetRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	payload := map[string]interface{}{
		"address":     strings.TrimSpace(req.Address),
		"description": strings.TrimSpace(req.Description),
		"criticality": 10,
	}
	bodyBytes, _ := json.Marshal(payload)

	resp, err := h.doRequest(http.MethodPost, "targets", bytes.NewReader(bodyBytes))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer resp.Body.Close()

	var resData map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&resData); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(resp.StatusCode, resData)
}

// StartScanRequest 發起掃描請求
type StartScanRequest struct {
	TargetID  string `json:"target_id" binding:"required"`
	ProfileID string `json:"profile_id"`
}

// StartScanTarget 發起 AWVS 掃描
func (h *AWVSHandler) StartScanTarget(targetID, profileID string) (map[string]interface{}, error) {
	targetID = strings.TrimSpace(targetID)
	if targetID == "" {
		return nil, fmt.Errorf("target_id 必填")
	}

	profileID = strings.TrimSpace(profileID)
	if profileID == "" {
		profileID = "11111111-1111-1111-1111-111111111111" // Full Scan
	}

	payload := map[string]interface{}{
		"target_id":  targetID,
		"profile_id": profileID,
		"schedule": map[string]interface{}{
			"disable":        false,
			"start_date":     nil,
			"time_sensitive": false,
		},
	}
	bodyBytes, _ := json.Marshal(payload)

	resp, err := h.doRequest(http.MethodPost, "scans", bytes.NewReader(bodyBytes))
	if err != nil {
		return nil, fmt.Errorf("發起掃描失敗: %w", err)
	}
	defer resp.Body.Close()

	var resData map[string]interface{}
	_ = json.NewDecoder(resp.Body).Decode(&resData)

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return resData, fmt.Errorf("AWVS 響應錯誤: 狀態碼 %d", resp.StatusCode)
	}

	return resData, nil
}

// StartScan 發起 AWVS 掃描（HTTP API）
func (h *AWVSHandler) StartScan(c *gin.Context) {
	var req StartScanRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	resData, err := h.StartScanTarget(req.TargetID, req.ProfileID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
			"data":    resData,
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    resData,
	})
}

// GetScanStatusInfo 獲取指定掃描任務狀態，或在 scanID 為空時列出所有掃描
func (h *AWVSHandler) GetScanStatusInfo(scanID string) (map[string]interface{}, error) {
	scanID = strings.TrimSpace(scanID)
	path := "scans"
	if scanID != "" {
		path = "scans/" + scanID
	}

	resp, err := h.doRequest(http.MethodGet, path, nil)
	if err != nil {
		return nil, fmt.Errorf("請求 AWVS scans 失敗: %w", err)
	}
	defer resp.Body.Close()

	var data map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, fmt.Errorf("解析 scans 回應失敗: %w", err)
	}

	return data, nil
}

// SyncRequest 同步漏洞請求
type SyncRequest struct {
	ProjectID string `json:"project_id"`
	TargetID  string `json:"target_id"`
}

// SyncVulnerabilitiesDirect 從 AWVS 拉取漏洞並匯入 JySecAI 本地資料庫（支援完整分頁與重複去重）
func (h *AWVSHandler) SyncVulnerabilitiesDirect(projectID, targetID string) (synced int, skipped int, totalInAwvs int, err error) {
	type awvsVulnItem struct {
		VulnID     string   `json:"vuln_id"`
		VTName     string   `json:"vt_name"`
		AffectsURL string   `json:"affects_url"`
		Severity   int      `json:"severity"`
		Status     string   `json:"status"`
		Tags       []string `json:"tags"`
		LastSeen   string   `json:"last_seen"`
	}

	var allVulnerabilities []awvsVulnItem
	cursor := ""
	visitedCursors := make(map[string]bool)
	const maxPages = 50 // 最多抓取 50 頁 (約 5000 條)

	for page := 0; page < maxPages; page++ {
		path := "vulnerabilities"
		var queryParams []string
		if strings.TrimSpace(targetID) != "" {
			queryParams = append(queryParams, "q=target_id:"+url.QueryEscape(strings.TrimSpace(targetID)))
		}
		if cursor != "" {
			queryParams = append(queryParams, "c="+url.QueryEscape(cursor))
		}
		if len(queryParams) > 0 {
			path += "?" + strings.Join(queryParams, "&")
		}

		resp, reqErr := h.doRequest(http.MethodGet, path, nil)
		if reqErr != nil {
			if len(allVulnerabilities) == 0 {
				return 0, 0, 0, fmt.Errorf("獲取 AWVS 漏洞列表失敗: %w", reqErr)
			}
			break
		}

		var listData struct {
			Vulnerabilities []awvsVulnItem `json:"vulnerabilities"`
			Pagination      struct {
				Count      int           `json:"count"`
				NextCursor *string       `json:"next_cursor"`
				Cursors    []interface{} `json:"cursors"`
			} `json:"pagination"`
		}

		decodeErr := json.NewDecoder(resp.Body).Decode(&listData)
		resp.Body.Close()
		if decodeErr != nil {
			if len(allVulnerabilities) == 0 {
				return 0, 0, 0, fmt.Errorf("解析 AWVS 漏洞回應失敗: %w", decodeErr)
			}
			break
		}

		totalInAwvs = listData.Pagination.Count
		allVulnerabilities = append(allVulnerabilities, listData.Vulnerabilities...)

		if len(listData.Vulnerabilities) == 0 {
			break
		}

		nextCursor := ""
		if listData.Pagination.NextCursor != nil && *listData.Pagination.NextCursor != "" {
			nextCursor = *listData.Pagination.NextCursor
		} else if len(listData.Pagination.Cursors) > 1 {
			if nextVal, ok := listData.Pagination.Cursors[1].(string); ok && nextVal != "" {
				nextCursor = nextVal
			}
		}

		if nextCursor == "" || nextCursor == cursor || visitedCursors[nextCursor] {
			break
		}
		visitedCursors[cursor] = true
		cursor = nextCursor
	}

	syncedCount := 0
	skippedCount := 0

	for _, awvsVuln := range allVulnerabilities {
		if strings.TrimSpace(awvsVuln.VTName) == "" {
			continue
		}

		var detailData struct {
			Description    string `json:"description"`
			Details        string `json:"details"`
			Request        string `json:"request"`
			Impact         string `json:"impact"`
			Recommendation string `json:"recommendation"`
		}
		if dResp, err := h.doRequest(http.MethodGet, "vulnerabilities/"+awvsVuln.VulnID, nil); err == nil {
			_ = json.NewDecoder(dResp.Body).Decode(&detailData)
			dResp.Body.Close()
		}

		sevStr := "info"
		switch awvsVuln.Severity {
		case 4:
			sevStr = "critical"
		case 3:
			sevStr = "high"
		case 2:
			sevStr = "medium"
		case 1:
			sevStr = "low"
		default:
			sevStr = "info"
		}

		vType := "Web Vulnerability"
		if len(awvsVuln.Tags) > 0 {
			vType = awvsVuln.Tags[0]
		}

		evidence := ""
		if strings.TrimSpace(detailData.Request) != "" {
			evidence = detailData.Request
		} else if strings.TrimSpace(detailData.Details) != "" {
			evidence = detailData.Details
		}

		reproSteps := ""
		if strings.TrimSpace(detailData.Request) != "" {
			reproSteps = "1. 發送 HTTP 請求至目標：\n```http\n" + detailData.Request + "\n```\n2. 觀察回應確認漏洞存在"
		} else {
			reproSteps = "1. 使用 AWVS 檢測目標位置: " + awvsVuln.AffectsURL
		}

		existing, err := h.db.FindVulnerabilityByTargetAndTitle(projectID, awvsVuln.AffectsURL, awvsVuln.VTName)
		if err == nil && existing != nil {
			needsUpdate := false
			if strings.TrimSpace(existing.Evidence) == "" && strings.TrimSpace(evidence) != "" {
				existing.Evidence = evidence
				needsUpdate = true
			}
			if strings.TrimSpace(existing.ReproSteps) == "" && strings.TrimSpace(reproSteps) != "" {
				existing.ReproSteps = reproSteps
				needsUpdate = true
			}
			if strings.TrimSpace(existing.ProjectID) == "" && strings.TrimSpace(projectID) != "" {
				existing.ProjectID = strings.TrimSpace(projectID)
				needsUpdate = true
			}
			if needsUpdate {
				_ = h.db.UpdateVulnerability(existing.ID, existing)
			}
			skippedCount++
			continue
		}

		vuln := &database.Vulnerability{
			ConversationID:  "",
			ProjectID:       strings.TrimSpace(projectID),
			ConversationTag: "awvs-scanner",
			TaskTag:         "awvs",
			Title:           awvsVuln.VTName,
			Description:     detailData.Description,
			Severity:        sevStr,
			Status:          "open",
			Type:            vType,
			Target:          awvsVuln.AffectsURL,
			Preconditions:   "AWVS 掃描目標: " + awvsVuln.AffectsURL,
			ReproSteps:      reproSteps,
			Evidence:        evidence,
			Impact:          detailData.Impact,
			Recommendation:  detailData.Recommendation,
			RetestNotes:     "使用 AWVS 或 JySecAI 自動生成 POC 進行複測",
		}

		if _, err := h.db.CreateVulnerability(vuln); err == nil {
			syncedCount++
		} else {
			skippedCount++
		}
	}

	return syncedCount, skippedCount, totalInAwvs, nil
}

// SyncVulnerabilities 從 AWVS 拉取漏洞並匯入 JySecAI 本地資料庫（HTTP API）
func (h *AWVSHandler) SyncVulnerabilities(c *gin.Context) {
	var req SyncRequest
	_ = c.ShouldBindJSON(&req)

	synced, skipped, total, err := h.SyncVulnerabilitiesDirect(req.ProjectID, req.TargetID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success":       true,
		"synced":        synced,
		"skipped":       skipped,
		"total_in_awvs": total,
		"message":       fmt.Sprintf("成功同步 %d 條 AWVS 漏洞到資料庫（已存在/跳過 %d 條）！", synced, skipped),
	})
}

// UpdateConfigRequest 更新 AWVS 設置
type UpdateAWVSConfigRequest struct {
	URL    string `json:"url"`
	APIKey string `json:"api_key"`
}

// UpdateConfig 動態更新 AWVS 伺服器位址與 API Key
func (h *AWVSHandler) UpdateConfig(c *gin.Context) {
	var req UpdateAWVSConfigRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	h.mu.Lock()
	if strings.TrimSpace(req.URL) != "" {
		h.baseURL = strings.TrimRight(strings.TrimSpace(req.URL), "/")
	}
	if strings.TrimSpace(req.APIKey) != "" {
		h.apiKey = strings.TrimSpace(req.APIKey)
	}
	currentURL := h.baseURL
	h.mu.Unlock()

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"url":     currentURL,
		"message": "AWVS 配置已更新",
	})
}
