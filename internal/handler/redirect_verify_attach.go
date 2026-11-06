package handler

import (
	"fmt"
	"net/http"
	"strings"
	"time"

	"jysecai/internal/database"
	"jysecai/internal/forbidden"
	"jysecai/internal/redirect"

	"go.uber.org/zap"
)

// ScanAttachedRedirectRequest 是掃描器附帶啟動批次跳轉植入的參數。
type ScanAttachedRedirectRequest struct {
	Text           string
	ProjectID      string
	ConversationID string
	OwnerUserID    string
}

// StartAttachedFromScan 在掃描開始時同步跑「巡站 → 植入 redirect.urls → 只讀 Location」。
//
// 植入的是平台設定的完整短鏈（例如 https://97y.me/tjneJ），探測不跟隨第二跳。
// 沒有 http(s) 目標、功能關閉、或沒有受控端點時不發請求。
func (h *RedirectVerifyHandler) StartAttachedFromScan(req ScanAttachedRedirectRequest) (*database.RedirectVerifyRun, error) {
	if h == nil || h.cfg == nil || !h.cfg.Redirect.AttachScanEffective() {
		return nil, nil
	}
	endpoints := redirect.NormalizeURLs(h.cfg.Redirect.URLs)
	if len(endpoints) == 0 {
		return nil, nil
	}
	seeds := redirect.FilterOwnCallbackURLs(redirect.ExtractHTTPURLs(req.Text), h.endpointHosts())
	if len(seeds) == 0 {
		return nil, nil
	}
	allowed, forbiddenTargets := forbidden.FilterTargets(seeds)
	if len(allowed) == 0 {
		if h.logger != nil {
			h.logger.Info("掃描附帶跳轉植入：目標均在禁區，已跳過", zap.Strings("forbidden", forbiddenTargets))
		}
		return nil, nil
	}

	run := &database.RedirectVerifyRun{
		Status:         database.RedirectVerifyStatusPending,
		Endpoints:      endpoints,
		Method:         http.MethodGet,
		Concurrency:    redirectVerifyDefaultConcurrency,
		Total:          len(allowed),
		ProjectID:      strings.TrimSpace(req.ProjectID),
		ConversationID: strings.TrimSpace(req.ConversationID),
		OwnerUserID:    strings.TrimSpace(req.OwnerUserID),
		AutoRecord:     true,
		CrawlEnabled:   true,
		CrawlMaxPages:  redirect.DefaultCrawlMaxPages,
		CrawlMaxDepth:  redirect.DefaultCrawlMaxDepth,
		SeedSource:     database.RedirectVerifySeedSourceManual,
		SeedCount:      len(allowed),
		Encoding:       redirect.PayloadEncodingNone,
		Repeat:         1,
	}
	if h.db == nil {
		return nil, fmt.Errorf("数据库不可用")
	}
	if err := h.db.CreateRedirectVerifyRun(run); err != nil {
		return nil, err
	}
	if run.OwnerUserID != "" {
		_ = h.db.SetResourceOwner("redirect_verify_run", run.ID, run.OwnerUserID)
		_ = h.db.AssignResourceToUser(run.OwnerUserID, "redirect_verify_run", run.ID)
	}
	if h.logger != nil {
		h.logger.Info("掃描附帶跳轉植入已啟動",
			zap.String("run_id", run.ID),
			zap.Int("seeds", len(allowed)),
			zap.String("endpoint", endpoints[0]),
			zap.String("conversation_id", run.ConversationID),
		)
	}
	go h.executeRun(run, allowed, time.Duration(redirectVerifyDefaultTimeoutSeconds)*time.Second)
	return run, nil
}
