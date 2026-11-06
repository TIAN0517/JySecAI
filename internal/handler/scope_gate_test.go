package handler

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"jysecai/internal/audit"
	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/multiagent"
	"jysecai/internal/scope"
	"jysecai/internal/security"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// Scope Registry P1：攔截點 A（handler 層 scope gate）的行為測試。
//
// 測試約束：
//   - 不對外送出任何真實網路請求（全部用 RFC 5737／RFC 2606 保留位址與網域）。
//   - 不碰正式資料庫（每個測試用自己的暫存 SQLite）。

// scopeGateTestTools 是測試用工具定義。
//
// 三支工具涵蓋三種動作類別：httpx（harmless_request，有宣告目標參數）、
// danger（destructive，永久封鎖類別）、freeform（未宣告 action_class＝arbitrary）。
func scopeGateTestTools() []config.ToolConfig {
	pos := 0
	return []config.ToolConfig{
		{
			Name:        "httpx",
			Command:     "true",
			Enabled:     true,
			ActionClass: scope.ActionHarmlessRequest,
			Parameters: []config.ParameterConfig{
				{Name: "targets", Type: "string", Target: true, TargetKind: "mixed", Position: &pos},
			},
		},
		{
			Name:        "danger",
			Command:     "true",
			Enabled:     true,
			ActionClass: scope.ActionDestructive,
			Parameters: []config.ParameterConfig{
				{Name: "targets", Type: "string", Target: true, TargetKind: "mixed", Position: &pos},
			},
		},
		{
			Name:    "freeform",
			Command: "true",
			Enabled: true,
			// 刻意不宣告 action_class：未宣告＝arbitrary（任意執行類）。
			Parameters: []config.ParameterConfig{
				{Name: "note", Type: "string"},
			},
		},
	}
}

// newScopeGateHandler 建立帶 scope 設定的測試用 AgentHandler。
func newScopeGateHandler(t *testing.T, enforcement string, tools []config.ToolConfig) (*AgentHandler, *database.DB) {
	t.Helper()
	tmp := t.TempDir()
	db, err := database.NewDB(filepath.Join(tmp, "scope-gate.sqlite"), zap.NewNop())
	if err != nil {
		t.Fatalf("建立測試資料庫失敗: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })

	cfg := &config.Config{
		Scope:    config.ScopeConfig{Enforcement: enforcement, DefaultOwner: "test-owner"},
		Security: config.SecurityConfig{Tools: tools},
	}
	h := &AgentHandler{
		db:          db,
		logger:      zap.NewNop(),
		config:      cfg,
		tasks:       NewAgentTaskManager(),
		hitlManager: NewHITLManager(db, zap.NewNop()),
	}
	if err := h.hitlManager.EnsureSchema(); err != nil {
		t.Fatalf("初始化 HITL schema 失敗: %v", err)
	}
	h.SetAudit(audit.NewService(db, cfg, zap.NewNop()))
	return h, db
}

// writeScopeTarget 寫入一筆常駐授權。
func writeScopeTarget(t *testing.T, db *database.DB, id, owner, targetType, targetValue string, classes []string) {
	t.Helper()
	err := database.UpsertScopeTarget(context.Background(), db, database.ScopeTarget{
		ID:            id,
		Owner:         owner,
		TargetType:    targetType,
		TargetValue:   targetValue,
		ActionClasses: classes,
		Conditions:    database.ScopeConditions{},
		Provenance:    database.ScopeProvenance{Source: "test", DecidedBy: "test", DecidedAt: time.Now()},
		Status:        database.ScopeTargetStatusActive,
		CreatedAt:     time.Now(),
	})
	if err != nil {
		t.Fatalf("寫入 scope target 失敗: %v", err)
	}
}

// countScopeTargets 統計常駐集筆數。
func countScopeTargets(t *testing.T, db *database.DB) int {
	t.Helper()
	var n int
	if err := db.QueryRow(`SELECT COUNT(*) FROM scope_targets`).Scan(&n); err != nil {
		t.Fatalf("統計 scope_targets 失敗: %v", err)
	}
	return n
}

// countScopeGrants 統計授權券筆數。
func countScopeGrants(t *testing.T, db *database.DB) int {
	t.Helper()
	var n int
	if err := db.QueryRow(`SELECT COUNT(*) FROM scope_grants`).Scan(&n); err != nil {
		t.Fatalf("統計 scope_grants 失敗: %v", err)
	}
	return n
}

// countScopeDenials 統計拒絕記憶筆數。
func countScopeDenials(t *testing.T, db *database.DB) int {
	t.Helper()
	var n int
	if err := db.QueryRow(`SELECT COUNT(*) FROM scope_denials`).Scan(&n); err != nil {
		t.Fatalf("統計 scope_denials 失敗: %v", err)
	}
	return n
}

// pendingScopeInterrupts 回傳所有 pending 的 scope_extension 中斷數。
func pendingScopeInterrupts(t *testing.T, db *database.DB) int {
	t.Helper()
	var n int
	if err := db.QueryRow(`SELECT COUNT(*) FROM hitl_interrupts WHERE status='pending' AND mode='scope_extension'`).Scan(&n); err != nil {
		t.Fatalf("統計 pending 中斷失敗: %v", err)
	}
	return n
}

// waitForScopeInterrupt 等待 scope_extension 中斷出現並回傳其 ID。
func waitForScopeInterrupt(t *testing.T, db *database.DB) string {
	t.Helper()
	deadline := time.Now().Add(10 * time.Second)
	for time.Now().Before(deadline) {
		var id string
		err := db.QueryRow(`SELECT id FROM hitl_interrupts WHERE status='pending' AND mode='scope_extension' ORDER BY created_at DESC LIMIT 1`).Scan(&id)
		if err == nil && id != "" {
			return id
		}
		time.Sleep(5 * time.Millisecond)
	}
	t.Fatal("等待 scope_extension 中斷逾時")
	return ""
}

// fetchScopePayload 讀出中斷 payload 並解析。
func fetchScopePayload(t *testing.T, db *database.DB, interruptID string) scopeInterruptPayload {
	t.Helper()
	var raw string
	if err := db.QueryRow(`SELECT COALESCE(payload,'') FROM hitl_interrupts WHERE id=?`, interruptID).Scan(&raw); err != nil {
		t.Fatalf("讀取中斷 payload 失敗: %v", err)
	}
	var payload scopeInterruptPayload
	if err := json.Unmarshal([]byte(raw), &payload); err != nil {
		t.Fatalf("解析中斷 payload 失敗: %v", err)
	}
	return payload
}

// TestScopeGateCoveredTargetPassesWithoutInterrupt：目標全覆蓋 → 不產生中斷，直接放行。
func TestScopeGateCoveredTargetPassesWithoutInterrupt(t *testing.T) {
	h, db := newScopeGateHandler(t, "enforce", scopeGateTestTools())
	writeScopeTarget(t, db, "scope_covered", "example-client", "host", "example.com", []string{scope.ActionHarmlessRequest})

	err := h.scopeGateEvaluate(context.Background(), nil, "conv-covered", "msg-covered", nil,
		"httpx", `{"targets":"example.com"}`)
	if err != nil {
		t.Fatalf("已授權的目標應該直接放行，得到錯誤: %v", err)
	}
	if n := pendingScopeInterrupts(t, db); n != 0 {
		t.Fatalf("已授權的目標不該產生中斷，得到 %d 筆", n)
	}
	if n := countScopeTargets(t, db); n != 1 {
		t.Fatalf("scope_targets 應維持 1 筆，得到 %d", n)
	}
}

// TestScopeGateUncoveredCreatesScopeExtension：有未覆蓋目標 + enforce → 產生中斷，
// payload 含 uncovered 與 adjacent。
func TestScopeGateUncoveredCreatesScopeExtension(t *testing.T) {
	h, db := newScopeGateHandler(t, "enforce", scopeGateTestTools())
	writeScopeTarget(t, db, "scope_adjacent", "example-client", "host", "api.example.com", []string{scope.ActionHarmlessRequest})

	done := make(chan error, 1)
	go func() {
		done <- h.scopeGateEvaluate(context.Background(), nil, "conv-uncovered", "msg-uncovered", nil,
			"httpx", `{"targets":"notapi.example.com"}`)
	}()

	interruptID := waitForScopeInterrupt(t, db)
	payload := fetchScopePayload(t, db, interruptID)

	if payload.Source != scopeGateSource {
		t.Fatalf("payload.source = %q, want %q", payload.Source, scopeGateSource)
	}
	if payload.ScopeExtension.ActionClass != scope.ActionHarmlessRequest {
		t.Fatalf("actionClass = %q", payload.ScopeExtension.ActionClass)
	}
	if payload.ScopeExtension.Reason != scopeReasonNotCovered {
		t.Fatalf("reason = %q, want %q", payload.ScopeExtension.Reason, scopeReasonNotCovered)
	}
	if payload.ScopeExtension.Arbitrary {
		t.Fatal("有宣告目標參數的工具不該是 arbitrary")
	}
	if len(payload.ScopeExtension.Uncovered) != 1 {
		t.Fatalf("uncovered 應有 1 筆，得到 %d", len(payload.ScopeExtension.Uncovered))
	}
	item := payload.ScopeExtension.Uncovered[0]
	if item.Host != "notapi.example.com" || item.Key != "notapi.example.com" || item.Kind != "host" {
		t.Fatalf("uncovered 欄位不完整: %+v", item)
	}
	if item.Raw != "notapi.example.com" {
		t.Fatalf("uncovered.raw = %q", item.Raw)
	}
	if len(payload.ScopeExtension.Adjacent) != 1 {
		t.Fatalf("adjacent 應有 1 筆，得到 %d", len(payload.ScopeExtension.Adjacent))
	}
	adjacent := payload.ScopeExtension.Adjacent[0]
	if adjacent.Host != "api.example.com" || adjacent.Owner != "example-client" {
		t.Fatalf("adjacent 不正確: %+v", adjacent)
	}
	if adjacent.GrantID != "scope_adjacent" || adjacent.Source != scope.SourceScopeTarget {
		t.Fatalf("adjacent 來源不正確: %+v", adjacent)
	}

	// 裁決：寫成常駐授權。
	if err := h.resolveScopeInterrupt(context.Background(), interruptID, scopeDecisionApprovePermanent, "已確認授權", nil, nil); err != nil {
		t.Fatalf("裁決失敗: %v", err)
	}
	if err := <-done; err != nil {
		t.Fatalf("批准後應原地續跑，得到錯誤: %v", err)
	}
	if n := countScopeTargets(t, db); n != 2 {
		t.Fatalf("批准後 scope_targets 應有 2 筆，得到 %d", n)
	}
	var owner, targetValue string
	var classes string
	if err := db.QueryRow(`SELECT owner, target_value, action_classes FROM scope_targets WHERE target_value='notapi.example.com'`).
		Scan(&owner, &targetValue, &classes); err != nil {
		t.Fatalf("讀取新授權失敗: %v", err)
	}
	if owner != "example-client" {
		t.Fatalf("owner = %q, want example-client（應沿用相鄰授權的 owner）", owner)
	}
	if !strings.Contains(classes, scope.ActionHarmlessRequest) {
		t.Fatalf("action_classes = %q", classes)
	}
	// provenance：source=scope_extension、decided_by=human、evidence_hash=中斷 ID。
	var provenance string
	if err := db.QueryRow(`SELECT provenance FROM scope_targets WHERE target_value='notapi.example.com'`).
		Scan(&provenance); err != nil {
		t.Fatalf("讀取 provenance 失敗: %v", err)
	}
	if !strings.Contains(provenance, `"source":"scope_extension"`) {
		t.Fatalf("provenance.source 應為 scope_extension，得到 %s", provenance)
	}
	if !strings.Contains(provenance, `"decided_by":"human"`) {
		t.Fatalf("provenance.decided_by 應為 human，得到 %s", provenance)
	}
	if !strings.Contains(provenance, interruptID) {
		t.Fatalf("provenance.evidence_hash 應含中斷 ID %s，得到 %s", interruptID, provenance)
	}
}

// TestScopeGateDerivedTargetAutoAuthorized：授權網域下的子網域自動進常駐集，不再跳授權卡片。
//
// 這是「衍生目標自動授權」的核心行為：書面授權涵蓋的是一個範圍，而攻擊面會長出
// 子網域。每一個都跳一次授權卡片是純操作負擔。
//
// 同時守住兩條界線：推導出來的授權沿用來源授權的 owner 與動作類別（不放大權限），
// 而且 provenance 標記為 scope_derived —— 稽核時要分得出「人裁決的」與「系統推導的」。
func TestScopeGateDerivedTargetAutoAuthorized(t *testing.T) {
	h, db := newScopeGateHandler(t, "enforce", scopeGateTestTools())
	writeScopeTarget(t, db, "scope_parent", "example-client", "host", "api.example.com", []string{scope.ActionHarmlessRequest})

	err := h.scopeGateEvaluate(context.Background(), nil, "conv-derived", "msg-derived", nil,
		"httpx", `{"targets":"new.api.example.com"}`)
	if err != nil {
		t.Fatalf("衍生目標不該被擋下: %v", err)
	}
	if n := pendingScopeInterrupts(t, db); n != 0 {
		t.Fatalf("衍生目標不該產生中斷，得到 %d 筆", n)
	}
	// 常駐集：來源授權 1 筆 + 推導出來的目標 1 筆。
	if n := countScopeTargets(t, db); n != 2 {
		t.Fatalf("scope_targets 應有 2 筆（來源＋推導），得到 %d", n)
	}
	var owner, classes, provenance string
	if err := db.QueryRow(`SELECT owner, action_classes, provenance FROM scope_targets WHERE target_value='new.api.example.com'`).
		Scan(&owner, &classes, &provenance); err != nil {
		t.Fatalf("讀取推導授權失敗: %v", err)
	}
	if owner != "example-client" {
		t.Fatalf("推導授權的 owner 應沿用來源授權: %q", owner)
	}
	if !strings.Contains(classes, scope.ActionHarmlessRequest) {
		t.Fatalf("推導授權的動作類別應沿用來源: %q", classes)
	}
	if !strings.Contains(provenance, `"source":"scope_derived"`) {
		t.Fatalf("provenance.source 應為 scope_derived，得到 %s", provenance)
	}
	if !strings.Contains(provenance, "api.example.com") {
		t.Fatalf("provenance 應記下推導自哪一筆授權，得到 %s", provenance)
	}
}

// TestScopeGateDerivedTargetDoesNotCoverSibling：同層兄弟網域不算衍生，仍要人工裁決。
//
// 只共享兩段標籤（example.com）但不是來源主機的子網域時（例如 notapi.example.com
// 對 api.example.com），不能自動授權 —— 那會把授權範圍撐到沒有書面依據的地方。
func TestScopeGateDerivedTargetDoesNotCoverSibling(t *testing.T) {
	h, db := newScopeGateHandler(t, "enforce", scopeGateTestTools())
	writeScopeTarget(t, db, "scope_parent", "example-client", "host", "api.example.com", []string{scope.ActionHarmlessRequest})

	go func() {
		_ = h.scopeGateEvaluate(context.Background(), nil, "conv-sibling", "msg-sibling", nil,
			"httpx", `{"targets":"notapi.example.com"}`)
	}()

	interruptID := waitForScopeInterrupt(t, db)
	payload := fetchScopePayload(t, db, interruptID)
	if len(payload.ScopeExtension.Uncovered) != 1 {
		t.Fatalf("兄弟網域不該被自動授權，uncovered 應有 1 筆，得到 %d", len(payload.ScopeExtension.Uncovered))
	}
	if n := countScopeTargets(t, db); n != 1 {
		t.Fatalf("不該寫入推導授權，scope_targets 應仍為 1 筆，得到 %d", n)
	}
}

// TestScopeGateForbiddenTargetIsRejected：命中禁區 → 直接拒絕，不產生中斷、不列入 uncovered。
func TestScopeGateForbiddenTargetIsRejected(t *testing.T) {
	h, db := newScopeGateHandler(t, "enforce", scopeGateTestTools())

	err := h.scopeGateEvaluate(context.Background(), nil, "conv-forbidden", "msg-forbidden", nil,
		"httpx", `{"targets":"app119.tfd.gov.tw"}`)
	if err == nil {
		t.Fatal("禁區目標必須被拒絕")
	}
	if !multiagent.IsHumanRejectError(err) {
		t.Fatalf("應該是軟拒絕（模型可繼續迭代），得到 %T", err)
	}
	if n := pendingScopeInterrupts(t, db); n != 0 {
		t.Fatalf("禁區目標不該產生中斷，得到 %d 筆", n)
	}

	result, resolveErr := scope.NewService(db).Resolve(context.Background(),
		[]string{"app119.tfd.gov.tw"}, scope.ActionHarmlessRequest, time.Now())
	if resolveErr != nil {
		t.Fatalf("scope 判定失敗: %v", resolveErr)
	}
	if len(result.Uncovered) != 0 {
		t.Fatalf("禁區目標不得列入 uncovered: %+v", result.Uncovered)
	}
	if len(result.Denied) != 1 || result.Denied[0].Reason != scope.ReasonForbidden {
		t.Fatalf("禁區目標應進 Denied（forbidden）: %+v", result.Denied)
	}
}

// TestScopeGatePermanentBlockedActionClassIsRejected：destructive／real_transaction → 直接拒絕。
func TestScopeGatePermanentBlockedActionClassIsRejected(t *testing.T) {
	for _, actionClass := range []string{scope.ActionDestructive, scope.ActionRealTransaction} {
		t.Run(actionClass, func(t *testing.T) {
			tools := scopeGateTestTools()
			tools[0].ActionClass = actionClass
			h, db := newScopeGateHandler(t, "enforce", tools)

			err := h.scopeGateEvaluate(context.Background(), nil, "conv-destructive", "msg-destructive", nil,
				"httpx", `{"targets":"example.com"}`)
			if err == nil {
				t.Fatalf("%s 類別必須被拒絕", actionClass)
			}
			if !multiagent.IsHumanRejectError(err) {
				t.Fatalf("應該是軟拒絕，得到 %T", err)
			}
			if n := pendingScopeInterrupts(t, db); n != 0 {
				t.Fatalf("%s 不該產生中斷，得到 %d 筆", actionClass, n)
			}
		})
	}
}

// TestScopeGateAuditModeRecordsButDoesNotBlock：audit 模式 → 稽核但不阻擋。
func TestScopeGateAuditModeRecordsButDoesNotBlock(t *testing.T) {
	h, db := newScopeGateHandler(t, "audit", scopeGateTestTools())

	err := h.scopeGateEvaluate(context.Background(), nil, "conv-audit", "msg-audit", nil,
		"httpx", `{"targets":"not-covered.example.org"}`)
	if err != nil {
		t.Fatalf("audit 模式不該阻擋，得到錯誤: %v", err)
	}
	if n := pendingScopeInterrupts(t, db); n != 0 {
		t.Fatalf("audit 模式不該產生中斷，得到 %d 筆", n)
	}
	var audits int
	if err := db.QueryRow(`SELECT COUNT(*) FROM audit_logs WHERE action='scope_resolve'`).Scan(&audits); err != nil {
		t.Fatalf("統計稽核失敗: %v", err)
	}
	if audits == 0 {
		t.Fatal("audit 模式應該寫入 scope_resolve 稽核")
	}
}

// TestScopeGateOffModeSkipsEvaluation：off 模式 → 完全不評估。
func TestScopeGateOffModeSkipsEvaluation(t *testing.T) {
	h, db := newScopeGateHandler(t, "off", scopeGateTestTools())

	// 連禁區目標都不評估（off＝維持既有行為）。
	err := h.scopeGateEvaluate(context.Background(), nil, "conv-off", "msg-off", nil,
		"httpx", `{"targets":"app119.tfd.gov.tw"}`)
	if err != nil {
		t.Fatalf("off 模式不該評估或阻擋，得到錯誤: %v", err)
	}
	if n := pendingScopeInterrupts(t, db); n != 0 {
		t.Fatalf("off 模式不該產生中斷，得到 %d 筆", n)
	}
	var audits int
	if err := db.QueryRow(`SELECT COUNT(*) FROM audit_logs WHERE action='scope_resolve'`).Scan(&audits); err != nil {
		t.Fatalf("統計稽核失敗: %v", err)
	}
	if audits != 0 {
		t.Fatalf("off 模式不該寫 scope_resolve 稽核，得到 %d 筆", audits)
	}
}

// TestScopeDecisionLanding：決策落地規則（approve_permanent／once／conditional／reject）。
func TestScopeDecisionLanding(t *testing.T) {
	t.Run("approve_once", func(t *testing.T) {
		h, db := newScopeGateHandler(t, "enforce", scopeGateTestTools())
		interruptID := startScopeGate(t, h, db, "conv-once", `{"targets":"once.example.com"}`)
		if err := h.resolveScopeInterrupt(context.Background(), interruptID, scopeDecisionApproveOnce, "只准這次", nil, nil); err != nil {
			t.Fatalf("裁決失敗: %v", err)
		}
		if n := countScopeGrants(t, db); n != 1 {
			t.Fatalf("scope_grants 應有 1 筆，得到 %d", n)
		}
		if n := countScopeTargets(t, db); n != 0 {
			t.Fatalf("approve_once 不該寫入 scope_targets，得到 %d", n)
		}
		var maxUses, targetValue, issuedBy string
		if err := db.QueryRow(`SELECT max_uses, target_value, issued_by FROM scope_grants`).Scan(&maxUses, &targetValue, &issuedBy); err != nil {
			t.Fatalf("讀取授權券失敗: %v", err)
		}
		if maxUses != "1" {
			t.Fatalf("max_uses = %s, want 1", maxUses)
		}
		if targetValue != "once.example.com" {
			t.Fatalf("target_value = %q", targetValue)
		}
		if issuedBy != "human:"+interruptID {
			t.Fatalf("issued_by = %q, want human:%s", issuedBy, interruptID)
		}
	})

	t.Run("approve_conditional", func(t *testing.T) {
		h, db := newScopeGateHandler(t, "enforce", scopeGateTestTools())
		interruptID := startScopeGate(t, h, db, "conv-cond", `{"targets":"cond.example.com"}`)
		conditions := &hitlScopeConditions{MaxUses: 3, ValidUntil: "2026-12-01T00:00:00Z"}
		if err := h.resolveScopeInterrupt(context.Background(), interruptID, scopeDecisionApproveConditional, "限三次", conditions, nil); err != nil {
			t.Fatalf("裁決失敗: %v", err)
		}
		var maxUses int
		var validUntil string
		if err := db.QueryRow(`SELECT max_uses, COALESCE(valid_until,'') FROM scope_grants`).Scan(&maxUses, &validUntil); err != nil {
			t.Fatalf("讀取授權券失敗: %v", err)
		}
		if maxUses != 3 {
			t.Fatalf("max_uses = %d, want 3", maxUses)
		}
		if validUntil == "" {
			t.Fatal("approve_conditional 應該寫入 valid_until")
		}
	})

	t.Run("approve_conditional_zero_max_uses", func(t *testing.T) {
		h, db := newScopeGateHandler(t, "enforce", scopeGateTestTools())
		interruptID := startScopeGate(t, h, db, "conv-cond0", `{"targets":"cond0.example.com"}`)
		if err := h.resolveScopeInterrupt(context.Background(), interruptID, scopeDecisionApproveConditional, "", &hitlScopeConditions{MaxUses: 0}, nil); err != nil {
			t.Fatalf("裁決失敗: %v", err)
		}
		var maxUses int
		if err := db.QueryRow(`SELECT max_uses FROM scope_grants`).Scan(&maxUses); err != nil {
			t.Fatalf("讀取授權券失敗: %v", err)
		}
		if maxUses != 1 {
			t.Fatalf("max_uses = %d, want 1（<=0 視為 1）", maxUses)
		}
	})

	t.Run("reject", func(t *testing.T) {
		h, db := newScopeGateHandler(t, "enforce", scopeGateTestTools())
		interruptID := startScopeGate(t, h, db, "conv-reject", `{"targets":"denied.example.com"}`)
		if err := h.resolveScopeInterrupt(context.Background(), interruptID, "reject", "不要碰這個", nil, nil); err != nil {
			t.Fatalf("裁決失敗: %v", err)
		}
		if n := countScopeDenials(t, db); n != 1 {
			t.Fatalf("scope_denials 應有 1 筆，得到 %d", n)
		}
		// 同一目標再次 Resolve → previously_denied
		result, err := scope.NewService(db).Resolve(context.Background(),
			[]string{"denied.example.com"}, scope.ActionHarmlessRequest, time.Now())
		if err != nil {
			t.Fatalf("scope 判定失敗: %v", err)
		}
		if len(result.Denied) != 1 || result.Denied[0].Reason != scope.ReasonPreviouslyDenied {
			t.Fatalf("被拒過的目標再次判定應為 previously_denied: %+v", result.Denied)
		}
	})
}

// TestScopeDecisionArbitraryRequiresDeclaredTargets：任意執行類工具批准時必須宣告目標。
func TestScopeDecisionArbitraryRequiresDeclaredTargets(t *testing.T) {
	h, db := newScopeGateHandler(t, "enforce", scopeGateTestTools())

	done := make(chan error, 1)
	go func() {
		done <- h.scopeGateEvaluate(context.Background(), nil, "conv-arbitrary", "msg-arbitrary", nil,
			"freeform", `{"note":"跑一個沒有目標參數的工具"}`)
	}()
	interruptID := waitForScopeInterrupt(t, db)
	payload := fetchScopePayload(t, db, interruptID)
	if !payload.ScopeExtension.Arbitrary {
		t.Fatal("未宣告 action_class 且沒有目標參數的工具應該是 arbitrary")
	}
	if payload.ScopeExtension.Reason != scopeReasonArbitrary {
		t.Fatalf("reason = %q, want %q", payload.ScopeExtension.Reason, scopeReasonArbitrary)
	}

	// 沒宣告目標就批准 → 決策失敗，且不得寫入任何 registry 資料。
	err := h.resolveScopeInterrupt(context.Background(), interruptID, scopeDecisionApprovePermanent, "好啦", nil, nil)
	if err == nil {
		t.Fatal("任意執行類工具未宣告目標就批准，決策必須失敗")
	}
	if n := countScopeTargets(t, db); n != 0 {
		t.Fatalf("決策失敗不得寫入 scope_targets，得到 %d", n)
	}
	if n := countScopeGrants(t, db); n != 0 {
		t.Fatalf("決策失敗不得寫入 scope_grants，得到 %d", n)
	}

	// 補上宣告目標後可以批准。
	if err := h.resolveScopeInterrupt(context.Background(), interruptID, scopeDecisionApprovePermanent, "好啦", nil,
		[]string{"declared.example.com"}); err != nil {
		t.Fatalf("宣告目標後應可批准: %v", err)
	}
	if n := countScopeTargets(t, db); n != 1 {
		t.Fatalf("批准後 scope_targets 應有 1 筆，得到 %d", n)
	}
	if err := <-done; err != nil {
		t.Fatalf("批准後應原地續跑，得到錯誤: %v", err)
	}
}

// TestExistingHitlDecisionVocabularyNotWidened：既有 approval／review_edit 模式的
// 決策詞彙沒有被 scope_extension 放寬（回歸測試）。
func TestExistingHitlDecisionVocabularyNotWidened(t *testing.T) {
	for _, tc := range []struct{ in, want string }{
		{"approval", "approval"},
		{"review_edit", "review_edit"},
		{"", "approval"},
		{"off", "off"},
		{"feedback", "approval"},
		{"scope_extension", "scope_extension"},
	} {
		if got := normalizeHitlMode(tc.in); got != tc.want {
			t.Fatalf("normalizeHitlMode(%q) = %q, want %q", tc.in, got, tc.want)
		}
	}

	h, db := newScopeGateHandler(t, "enforce", scopeGateTestTools())
	for _, mode := range []string{"approval", "review_edit"} {
		p, err := h.hitlManager.CreatePendingInterrupt("conv-legacy", "msg-legacy", mode, "httpx", "", "{}", "human")
		if err != nil {
			t.Fatalf("建立 %s 中斷失敗: %v", mode, err)
		}
		for _, decision := range []string{scopeDecisionApprovePermanent, scopeDecisionApproveOnce, scopeDecisionApproveConditional} {
			if err := h.hitlManager.ResolveInterrupt(p.InterruptID, decision, "", nil); err == nil {
				t.Fatalf("%s 模式不該接受 %s", mode, decision)
			}
		}
	}
	// scope 決策詞彙不得寫進常駐集（決策被擋下 → 沒有任何寫入）。
	if n := countScopeTargets(t, db); n != 0 {
		t.Fatalf("既有模式被拒的決策不得寫入 scope_targets，得到 %d", n)
	}
	if n := countScopeGrants(t, db); n != 0 {
		t.Fatalf("既有模式被拒的決策不得寫入 scope_grants，得到 %d", n)
	}
}

// TestDecideHITLInterruptScopeExtension：HTTP 層的 scope_extension 決策（前端契約）。
func TestDecideHITLInterruptScopeExtension(t *testing.T) {
	h, db := newScopeGateHandler(t, "enforce", scopeGateTestTools())
	interruptID := startScopeGate(t, h, db, "conv-http", `{"targets":"http.example.com"}`)

	gin.SetMode(gin.TestMode)
	router := gin.New()
	router.Use(func(c *gin.Context) {
		c.Set(security.ContextSessionKey, security.Session{
			UserID:      "u1",
			Username:    "operator",
			Permissions: map[string]bool{"hitl:read": true, "hitl:write": true},
			Scope:       database.RBACScopeAll,
		})
		c.Next()
	})
	router.POST("/api/hitl/decision", h.DecideHITLInterrupt)

	body := `{"interruptId":"` + interruptID + `","decision":"approve_conditional","comment":"限三次",` +
		`"scopeConditions":{"owner":"http-owner","actionClasses":["harmless_request"],"maxUses":2,"validUntil":"2026-12-01T00:00:00Z"},` +
		`"scopeTargets":["declared-http.example.com"]}`
	req := httptest.NewRequest(http.MethodPost, "/api/hitl/decision", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200: %s", w.Code, w.Body.String())
	}
	if !strings.Contains(w.Body.String(), `"ok":true`) {
		t.Fatalf("回應內容 = %s", w.Body.String())
	}
	// arbitrary=false：uncovered 與宣告的目標都會各寫一列授權券。
	var grants int
	if err := db.QueryRow(`SELECT COUNT(*) FROM scope_grants`).Scan(&grants); err != nil {
		t.Fatalf("統計授權券失敗: %v", err)
	}
	if grants != 2 {
		t.Fatalf("scope_grants 應有 2 筆（uncovered + 宣告目標），得到 %d", grants)
	}
	var maxUses int
	var issuedBy, targetValue string
	if err := db.QueryRow(`SELECT max_uses, issued_by, target_value FROM scope_grants WHERE target_value='http.example.com'`).
		Scan(&maxUses, &issuedBy, &targetValue); err != nil {
		t.Fatalf("讀取授權券失敗: %v", err)
	}
	if maxUses != 2 {
		t.Fatalf("max_uses = %d, want 2", maxUses)
	}
	if issuedBy != "human:"+interruptID {
		t.Fatalf("issued_by = %q, want human:%s", issuedBy, interruptID)
	}
	if err := db.QueryRow(`SELECT COUNT(*) FROM scope_grants WHERE target_value='declared-http.example.com'`).Scan(&grants); err != nil {
		t.Fatalf("統計宣告目標的授權券失敗: %v", err)
	}
	if grants != 1 {
		t.Fatalf("宣告的目標也應各寫一列授權券，得到 %d", grants)
	}
}

// TestDecideHITLInterruptRejectsScopeVocabularyForLegacyMode：既有模式的中斷
// 不得被 scope 決策詞彙放寬（HTTP 層回歸）。
func TestDecideHITLInterruptRejectsScopeVocabularyForLegacyMode(t *testing.T) {
	h, db := newScopeGateHandler(t, "enforce", scopeGateTestTools())
	p, err := h.hitlManager.CreatePendingInterrupt("conv-legacy-http", "msg-legacy", "approval", "httpx", "", "{}", "human")
	if err != nil {
		t.Fatalf("建立中斷失敗: %v", err)
	}

	gin.SetMode(gin.TestMode)
	router := gin.New()
	router.Use(func(c *gin.Context) {
		c.Set(security.ContextSessionKey, security.Session{
			UserID:      "u1",
			Username:    "operator",
			Permissions: map[string]bool{"hitl:read": true, "hitl:write": true},
			Scope:       database.RBACScopeAll,
		})
		c.Next()
	})
	router.POST("/api/hitl/decision", h.DecideHITLInterrupt)

	body := `{"interruptId":"` + p.InterruptID + `","decision":"approve_permanent"}`
	req := httptest.NewRequest(http.MethodPost, "/api/hitl/decision", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusConflict {
		t.Fatalf("status = %d, want 409: %s", w.Code, w.Body.String())
	}
	if n := countScopeTargets(t, db); n != 0 {
		t.Fatalf("既有模式不得寫入 scope_targets，得到 %d", n)
	}
}

// startScopeGate 啟動 scope gate（背景執行）並等待中斷出現，回傳中斷 ID。
func startScopeGate(t *testing.T, h *AgentHandler, db *database.DB, conversationID, arguments string) string {
	t.Helper()
	go func() {
		_ = h.scopeGateEvaluate(context.Background(), nil, conversationID, "msg-"+conversationID, nil,
			"httpx", arguments)
	}()
	return waitForScopeInterrupt(t, db)
}
