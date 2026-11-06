package handler

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"

	"jysecai/internal/audit"
	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/multiagent"
	"jysecai/internal/scope"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go.uber.org/zap"
)

// Scope 執行閘（攔截點 A）。
//
// 為什麼在這裡
// ------------
// Eino 的工具中介層（internal/multiagent/hitl_middleware.go 的 hitlToolCallMiddleware）
// 會呼叫 ctx 裡的 HITLToolInterceptor，而 handler 端的實作是
// (*AgentHandler).interceptHITLForEinoTool —— 那是所有 Eino 工具呼叫的單一漏斗。
// 把 scope gate 插在它開頭（既有 HITL 人工審批之前），就得到：
//
//	Eino 工具呼叫 → hitlToolCallMiddleware → HITLToolInterceptor
//	  → interceptHITLForEinoTool
//	      → 【P1】scopeGate：解析目標 → scope.Resolve
//	          → 命中 Denied        → 直接擋（軟拒絕回模型）
//	          → 有 Uncovered 且 enforce → 建立 scope_extension 中斷 → 等裁決 → 寫 registry → 原地續跑
//	          → 其餘                → 放行
//	      → 【既有】HITL 人工審批
//	      → 工具實際執行
//
// 為什麼用「軟拒絕」而不是回 error
// --------------------------------
// hitlToolCallMiddleware 只把 multiagent.NewHumanRejectError 轉成軟拒絕（讓模型
// 看到訊息後繼續迭代）；其他 error 會直接讓整個工具呼叫失敗、中斷 agent loop。
// scope 拒絕必須是軟拒絕——模型要知道自己為什麼被擋，才會改目標而不是一直重試。

const (
	// scopeGateSource 是 scope 中斷 payload 的 source 標記。
	scopeGateSource = "scope_gate"
	// scopeExtensionMode 是 scope 中斷使用的 HITL mode（沿用 hitl_interrupts 表）。
	scopeExtensionMode = "scope_extension"
	// scopeProvenanceSource 是 scope_extension 寫進 registry 的 provenance.source。
	scopeProvenanceSource = "scope_extension"
	// scopeProvenanceSourceDerived 是「衍生目標自動授權」寫進 registry 的 provenance.source。
	//
	// 與 scope_extension 分開，是為了讓稽核能分辨：這一筆是操作者親手裁決的，
	// 那一筆是系統推導出來的。兩者的證據強度不同，不能混為一談。
	scopeProvenanceSourceDerived = "scope_derived"
)

// scope_extension 專屬的決策詞彙（既有 approval／review_edit 模式不接受這些值）。
const (
	// scopeDecisionApprovePermanent 寫入 scope_targets（常駐集）。
	scopeDecisionApprovePermanent = "approve_permanent"
	// scopeDecisionApproveOnce 寫入 scope_grants（max_uses=1）。
	scopeDecisionApproveOnce = "approve_once"
	// scopeDecisionApproveConditional 寫入 scope_grants（帶 max_uses／valid_until）。
	scopeDecisionApproveConditional = "approve_conditional"
)

// scope 中斷 payload 的原因字串。
const (
	// scopeReasonNotCovered 是「目標沒有被任何 scope 涵蓋」。
	scopeReasonNotCovered = "not_covered_by_any_scope"
	// scopeReasonArbitrary 是「任意執行類工具，必須由操作者宣告目標」。
	scopeReasonArbitrary = "arbitrary_execution_requires_declared_targets"
)

// scopeExtensionPayload 是 scope_extension 中斷 payload 的 scopeExtension 區段。
//
// 欄位名是前端契約，不可更改（前端依此渲染卡片）。
type scopeExtensionPayload struct {
	// ActionClass 是本次工具呼叫的動作類別。
	ActionClass string `json:"actionClass"`
	// Reason 是未覆蓋的原因（not_covered_by_any_scope / arbitrary_...）。
	Reason string `json:"reason"`
	// Arbitrary true 代表這是「任意執行類」工具，批准前必須宣告目標清單。
	Arbitrary bool `json:"arbitrary"`
	// DeclaredTargets 是操作者宣告的目標清單（由決策請求帶回）。
	DeclaredTargets []string `json:"declaredTargets"`
	// Uncovered 是沒有被任何 scope 涵蓋的目標。
	Uncovered []scopeTargetItem `json:"uncovered"`
	// Adjacent 是與未覆蓋目標共享最長後綴的既有授權（給操作者當線索）。
	Adjacent []scopeAdjacentItem `json:"adjacent"`
	// Denied 是被拒絕的目標（禁區／永久封鎖類別／拒絕記憶）。
	Denied []scopeDeniedItem `json:"denied"`
}

// scopeTargetItem 是 payload 裡的一個目標（欄位全部填滿，前端直接顯示）。
type scopeTargetItem struct {
	Raw  string `json:"raw"`
	Host string `json:"host"`
	Port string `json:"port"`
	Kind string `json:"kind"`
	Key  string `json:"key"`
	URL  string `json:"url"`
}

// scopeAdjacentItem 是相鄰授權的線索。
type scopeAdjacentItem struct {
	Host          string   `json:"host"`
	Owner         string   `json:"owner"`
	GrantID       string   `json:"grantId"`
	Source        string   `json:"source"`
	ActionClasses []string `json:"actionClasses"`
	ValidUntil    string   `json:"validUntil"`
}

// scopeDeniedItem 是被拒絕的目標。
type scopeDeniedItem struct {
	Host   string `json:"host"`
	Reason string `json:"reason"`
	Detail string `json:"detail"`
}

// scopeInterruptPayload 是存進 hitl_interrupts.payload 的完整 JSON。
type scopeInterruptPayload struct {
	Source         string                 `json:"source"`
	ToolName       string                 `json:"toolName"`
	Arguments      string                 `json:"arguments"`
	ArgumentsObj   map[string]interface{} `json:"argumentsObj"`
	ScopeExtension scopeExtensionPayload  `json:"scopeExtension"`
}

// scopeGateEvaluate 是攔截點 A 的核心。
//
// 回傳 nil 代表放行；回傳錯誤代表軟拒絕（訊息會回給模型）。
// enforcement=off 時完全不做任何評估（維持既有行為，平台不會被空 registry 鎖死）。
func (h *AgentHandler) scopeGateEvaluate(runCtx context.Context, cancelRun context.CancelCauseFunc, conversationID, assistantMessageID string, sendEventFunc func(eventType, message string, data interface{}), toolName, arguments string) error {
	if h == nil {
		return nil
	}
	mode := h.scopeEnforcementMode()
	if mode == config.ScopeEnforcementOff {
		return nil
	}

	toolCfg := h.scopeToolConfig(toolName)
	actionClass := scope.ActionArbitrary
	var params []config.ParameterConfig
	if toolCfg != nil {
		params = toolCfg.Parameters
		if declared := strings.TrimSpace(toolCfg.ActionClass); declared != "" {
			actionClass = declared
		}
	}

	argsObj := map[string]interface{}{}
	if strings.TrimSpace(arguments) != "" {
		_ = json.Unmarshal([]byte(arguments), &argsObj)
	}
	if argsObj == nil {
		argsObj = map[string]interface{}{}
	}

	svc := h.scopeService()
	if svc == nil {
		// 沒有資料庫連線就沒有 registry 可查：enforce 模式 fail closed。
		if mode == config.ScopeEnforcementEnforce {
			return multiagent.NewHumanRejectError(
				"scope registry 尚未就緒（缺少資料庫連線），已依 fail-closed 原則拒絕本次工具呼叫；請聯絡管理員修復後再試。")
		}
		return nil
	}

	// 本機檔案分析／離線重放不碰網路，不需要 scope 檢查。
	// 與 executor 層（攔截點 B）同一條規則：兩層的判定不一致會出現
	// 「閘放行、執行器擋下」或反過來的落差。
	if actionClass == scope.ActionLocalAnalysis || actionClass == scope.ActionOfflineReplay {
		return nil
	}

	// 永久封鎖的動作類別：不論有沒有目標都擋下來。
	if scope.IsPermanentBlockedActionClass(actionClass) {
		denied := []scope.Denial{{
			Target: scope.Target{Raw: toolName},
			Reason: scope.ReasonPermanentBlock,
			Detail: "動作類別 " + actionClass + " 屬永久封鎖，任何 scope／授權券都無法授權",
		}}
		h.recordScopeAudit(nil, toolName, actionClass, mode, nil, denied, nil, "", "", "")
		return multiagent.NewHumanRejectError(scopeDeniedMessage(denied))
	}

	targets, arbitrary, extractErr := scope.ExtractTargets(toolName, params, argsObj, scopeAdditionalArgs(argsObj), "")
	if extractErr != nil {
		// 目標解析失敗＝無法確認這次會碰到誰：fail closed。
		if mode == config.ScopeEnforcementEnforce {
			h.recordScopeAudit(nil, toolName, actionClass, mode, nil, nil, nil, "", "", "")
			return multiagent.NewHumanRejectError(
				"無法解析本次工具呼叫會接觸的目標（" + extractErr.Error() + "），已依 fail-closed 原則拒絕；請明確指定目標後再試。")
		}
		h.recordScopeAudit(nil, toolName, actionClass, mode, nil, nil, nil, "", "", "")
		return nil
	}

	result, resolveErr := svc.Resolve(runCtx, targets, actionClass, time.Now())
	if resolveErr != nil {
		if mode == config.ScopeEnforcementEnforce {
			h.recordScopeAudit(nil, toolName, actionClass, mode, nil, nil, nil, "", "", "")
			return multiagent.NewHumanRejectError(
				"scope registry 查詢失敗（" + resolveErr.Error() + "），已依 fail-closed 原則拒絕本次工具呼叫。")
		}
		h.recordScopeAudit(nil, toolName, actionClass, mode, nil, nil, nil, "", "", "")
		return nil
	}

	// 衍生目標自動授權：未被涵蓋、但可由既有常駐授權推導出來的目標（授權網域下的
	// 子網域、同一授權網段內的位址），直接寫進常駐集，不再逐一跳出授權卡片。
	// 推導不改變判定結果本身：禁區與永久封鎖在 Resolve 階段就已經擋掉了。
	if len(result.Uncovered) > 0 {
		result = h.autoGrantDerivedTargets(runCtx, svc, result)
	}

	// 命中禁區／拒絕記憶／永久封鎖：直接拒絕，不產生中斷。
	if len(result.Denied) > 0 {
		h.recordScopeAudit(nil, toolName, actionClass, mode, result.Covered, result.Denied, result.Uncovered, "", "", "")
		return multiagent.NewHumanRejectError(scopeDeniedMessage(result.Denied))
	}

	// audit 模式：只記錄，不阻擋。
	if mode == config.ScopeEnforcementAudit {
		h.recordScopeAudit(nil, toolName, actionClass, mode, result.Covered, result.Denied, result.Uncovered, "", "", "")
		return nil
	}

	// enforce 模式：未覆蓋目標 → 中斷請操作者裁決。
	if !arbitrary && len(result.Uncovered) == 0 {
		h.recordScopeAudit(nil, toolName, actionClass, mode, result.Covered, result.Denied, result.Uncovered, "", "", "")
		return nil
	}

	reason := scopeReasonNotCovered
	if arbitrary {
		reason = scopeReasonArbitrary
	}
	return h.requestScopeExtension(runCtx, cancelRun, conversationID, assistantMessageID, sendEventFunc,
		toolName, arguments, argsObj, actionClass, reason, arbitrary, result, svc)
}

// autoGrantDerivedTargets 把「可由既有常駐授權推導出來」的目標自動寫進常駐集。
//
// 為什麼要有這一步：書面授權涵蓋的是一個範圍，但攻擊面會長 —— 授權 example.com 之後
// DNS 會冒出 api.example.com，DNS 記錄裡的 10.20.0.7 也在同一個授權網段裡。這些目標
// 每一個都要人工裁決一次授權卡片，是純操作負擔；但它們確實落在同一份授權的範圍語意內。
//
// 邊界（刻意保守）：
//   - 只從仍然有效的常駐授權推導；不從一次性授權券推導，不從過期／撤銷的授權推導。
//   - 推導出來的目標沿用來源授權的 owner、動作類別與期間 —— 不放大權限，也不延長期間。
//   - 禁區與永久封鎖的動作類別在 Resolve 階段就擋掉了，不會走到這裡。
//
// 稽核軌跡：寫入時 provenance.source = scope_derived，並記下推導自哪一筆授權，
// 所以「這個目標是被推導出來的、依據是什麼」在稽核時查得到。
func (h *AgentHandler) autoGrantDerivedTargets(ctx context.Context, svc *scope.Service, result scope.Result) scope.Result {
	if h == nil || svc == nil || len(result.Uncovered) == 0 {
		return result
	}
	now := time.Now()
	derived, err := svc.DerivedTargets(ctx, result.Uncovered, now)
	if err != nil || len(derived) == 0 {
		return result
	}

	granted := map[string]bool{}
	for _, item := range derived {
		targetType, targetValue := scopeTargetTypeValue(item.Target)
		if err := database.UpsertScopeTarget(ctx, h.db, database.ScopeTarget{
			ID:            "scope_derived_" + strings.ReplaceAll(uuid.New().String(), "-", ""),
			Owner:         item.SourceOwner,
			TargetType:    targetType,
			TargetValue:   targetValue,
			ActionClasses: item.ActionClasses,
			Conditions:    database.ScopeConditions{},
			ValidFrom:     item.ValidFrom,
			ValidUntil:    item.ValidUntil,
			Provenance: database.ScopeProvenance{
				Source:    scopeProvenanceSourceDerived,
				DecidedBy: "auto-derived",
				DecidedAt: now,
				Note:      "衍生自常駐授權 " + item.SourceValue + "（" + item.SourceID + "）",
			},
			Status:    database.ScopeTargetStatusActive,
			CreatedAt: now,
		}); err != nil {
			// 寫入失敗就當作沒推導：寧可回到人工裁決，也不要留下半套狀態。
			if h.logger != nil {
				h.logger.Warn("衍生目標自動授權寫入失敗", zap.Error(err), zap.String("target", item.Target.Key()))
			}
			continue
		}
		granted[item.Target.Key()] = true
		result.Covered = append(result.Covered, scope.Match{
			Target:        item.Target,
			GrantID:       item.SourceID,
			Source:        scope.SourceScopeTarget,
			Owner:         item.SourceOwner,
			ActionClasses: item.ActionClasses,
		})
	}

	if len(granted) == 0 {
		return result
	}
	remaining := make([]scope.Target, 0, len(result.Uncovered))
	for _, target := range result.Uncovered {
		if granted[target.Key()] {
			continue
		}
		remaining = append(remaining, target)
	}
	result.Uncovered = remaining
	return result
}

// requestScopeExtension 建立 scope_extension 中斷、等待操作者裁決。
//
// 決策落地（寫 registry）在 DecideHITLInterrupt 端完成，並且是「先寫完 registry
// 才回傳批准」——這樣原地續跑時 executor 的兜底檢查（攔截點 B）才查得到授權。
func (h *AgentHandler) requestScopeExtension(runCtx context.Context, cancelRun context.CancelCauseFunc, conversationID, assistantMessageID string, sendEventFunc func(eventType, message string, data interface{}), toolName, arguments string, argsObj map[string]interface{}, actionClass, reason string, arbitrary bool, result scope.Result, svc *scope.Service) error {
	adjacent := []scopeAdjacentItem{}
	if !arbitrary {
		if items, err := svc.AdjacentScopes(runCtx, result.Uncovered); err == nil {
			for _, item := range items {
				adjacent = append(adjacent, scopeAdjacentItem{
					Host:          item.Host,
					Owner:         item.Owner,
					GrantID:       item.GrantID,
					Source:        item.Source,
					ActionClasses: item.ActionClasses,
					ValidUntil:    item.ValidUntil,
				})
			}
		} else if h.logger != nil {
			h.logger.Warn("查詢相鄰授權失敗", zap.Error(err), zap.String("toolName", toolName))
		}
	}

	extension := scopeExtensionPayload{
		ActionClass:     actionClass,
		Reason:          reason,
		Arbitrary:       arbitrary,
		DeclaredTargets: []string{},
		Uncovered:       []scopeTargetItem{},
		Adjacent:        adjacent,
		Denied:          []scopeDeniedItem{},
	}
	if !arbitrary {
		for _, target := range result.Uncovered {
			extension.Uncovered = append(extension.Uncovered, scopeTargetToItem(target))
		}
	}
	for _, denial := range result.Denied {
		extension.Denied = append(extension.Denied, scopeDeniedItem{
			Host:   denial.Target.Host,
			Reason: denial.Reason,
			Detail: denial.Detail,
		})
	}

	payload := scopeInterruptPayload{
		Source:         scopeGateSource,
		ToolName:       toolName,
		Arguments:      arguments,
		ArgumentsObj:   argsObj,
		ScopeExtension: extension,
	}
	payloadRaw, err := json.Marshal(payload)
	if err != nil {
		return multiagent.NewHumanRejectError("scope 中斷 payload 建構失敗：" + err.Error())
	}

	p, err := h.hitlManager.createScopePendingInterrupt(conversationID, assistantMessageID, toolName, "", string(payloadRaw))
	if err != nil {
		if h.logger != nil {
			h.logger.Warn("建立 scope 中斷失敗", zap.Error(err), zap.String("toolName", toolName))
		}
		return multiagent.NewHumanRejectError("scope 中斷建立失敗，已依 fail-closed 原則拒絕本次工具呼叫：" + err.Error())
	}

	timeout := h.scopeExtensionTimeout(conversationID)
	createdAt := time.Now().UTC()
	expiresAt := (*time.Time)(nil)
	if timeout > 0 {
		exp := createdAt.Add(timeout)
		expiresAt = &exp
	}

	emit := func(eventType, message string, eventData map[string]interface{}) {
		clientData := enrichProgressEventData(eventData, conversationID, assistantMessageID)
		if sendEventFunc != nil {
			sendEventFunc(eventType, message, clientData)
		}
		if strings.TrimSpace(assistantMessageID) != "" && h.db != nil {
			if err := h.db.AddProcessDetail(assistantMessageID, conversationID, eventType, message, clientData); err != nil && h.logger != nil {
				h.logger.Warn("保存 scope 過程詳情失敗", zap.Error(err), zap.String("eventType", eventType))
			}
		}
	}

	emit("hitl_interrupt", "目標不在授權範圍內，請裁決是否授權", map[string]interface{}{
		"conversationId": conversationID,
		"interruptId":    p.InterruptID,
		"mode":           scopeExtensionMode,
		"toolName":       toolName,
		"toolCallId":     "",
		"reviewer":       "human",
		"status":         "pending",
		"createdAt":      createdAt,
		"timeoutSeconds": int(timeout / time.Second),
		"expiresAt":      expiresAt,
		"payload":        payload,
	})

	decision, waitErr := h.hitlManager.waitDecision(runCtx, p, timeout)
	if waitErr != nil {
		// 工作被取消：不寫拒絕記憶（取消不是操作者的裁決），但工具確實不該執行。
		emit("hitl_rejected", "任務已取消，scope 授權未取得", map[string]interface{}{
			"conversationId": conversationID,
			"interruptId":    p.InterruptID,
			"toolName":       toolName,
			"mode":           scopeExtensionMode,
			"status":         "cancelled",
			"decision":       "reject",
			"comment":        "task cancelled",
			"decidedBy":      "system",
			"reviewer":       "human",
			"scopeExtension": extension,
		})
		return waitErr
	}

	timedOut := strings.Contains(strings.ToLower(decision.Comment), "timeout")
	if timedOut {
		// 逾時＝視為拒絕，並記住（下次同一目標直接拒、不再打擾操作者）。
		h.writeScopeDenials(runCtx, &extension, h.scopeOwnerFromExtension(&extension), decision.Comment)
		// 事件裡的 scopeExtension 保留原本的未覆蓋清單（前端要顯示「逾時已拒絕並記住」），
		// 逾時訊號由 status=timeout／decidedBy=system 帶出，不改動 reason。
		emit("hitl_rejected", "授權裁決逾時，已自動拒絕並記住此目標", map[string]interface{}{
			"conversationId": conversationID,
			"interruptId":    p.InterruptID,
			"toolName":       toolName,
			"mode":           scopeExtensionMode,
			"status":         "timeout",
			"decision":       "reject",
			"comment":        decision.Comment,
			"decidedBy":      "system",
			"reviewer":       "human",
			"scopeExtension": extension,
		})
		h.recordScopeAudit(nil, toolName, actionClass, config.ScopeEnforcementEnforce, result.Covered, result.Denied, result.Uncovered, "reject", "system", p.InterruptID)
		return multiagent.NewHumanRejectError(scopeRejectedMessage(decision.Comment))
	}

	if decision.Decision == "reject" {
		// 明確拒絕：拒絕記憶由 DecideHITLInterrupt 端在回傳決定之前寫入
		//（被「取消卡片」 dismiss 的情況不會寫拒絕記憶——取消不是裁決）。
		emit("hitl_rejected", "人工拒絕本次目標授權", map[string]interface{}{
			"conversationId": conversationID,
			"interruptId":    p.InterruptID,
			"toolName":       toolName,
			"mode":           scopeExtensionMode,
			"status":         "decided",
			"decision":       "reject",
			"comment":        decision.Comment,
			"decidedBy":      "human",
			"reviewer":       "human",
			"scopeExtension": extension,
		})
		h.recordScopeAudit(nil, toolName, actionClass, config.ScopeEnforcementEnforce, result.Covered, result.Denied, result.Uncovered, "reject", "human", p.InterruptID)
		return multiagent.NewHumanRejectError(scopeRejectedMessage(decision.Comment))
	}

	// 批准：registry 已由 DecideHITLInterrupt 寫入完成，原地續跑（不改參數）。
	emit("hitl_resumed", "已授權此目標，繼續執行", map[string]interface{}{
		"conversationId": conversationID,
		"interruptId":    p.InterruptID,
		"toolName":       toolName,
		"mode":           scopeExtensionMode,
		"status":         "decided",
		"decision":       decision.Decision,
		"comment":        decision.Comment,
		"decidedBy":      "human",
		"reviewer":       "human",
		"scopeExtension": extension,
	})
	h.recordScopeAudit(nil, toolName, actionClass, config.ScopeEnforcementEnforce, result.Covered, result.Denied, result.Uncovered, decision.Decision, "human", p.InterruptID)
	return nil
}

// applyScopeDecision 把操作者的裁決寫進 scope registry。
//
// 這是「先寫 registry、再回傳批准」的落點：寫完之後 executor 的兜底檢查才查得到。
func (h *AgentHandler) applyScopeDecision(ctx context.Context, interruptID string, payload *scopeInterruptPayload, decision, comment string, conditions *hitlScopeConditions, declared []string) error {
	if payload == nil {
		return errors.New("scope 中斷 payload 不完整")
	}
	extension := payload.ScopeExtension
	actionClass := strings.TrimSpace(extension.ActionClass)
	if actionClass == "" {
		actionClass = scope.ActionArbitrary
	}

	// 目標集合：未覆蓋目標 + 操作者宣告的目標（正規化後以 Key 去重）。
	targets := make([]scope.Target, 0, len(extension.Uncovered)+len(declared))
	seen := make(map[string]struct{})
	appendTarget := func(target scope.Target) {
		key := target.Key()
		if key == "" {
			return
		}
		if _, dup := seen[key]; dup {
			return
		}
		seen[key] = struct{}{}
		targets = append(targets, target)
	}
	if !extension.Arbitrary {
		for _, item := range extension.Uncovered {
			appendTarget(scope.NormalizeTarget(item.Raw))
		}
	}
	for _, raw := range declared {
		trimmed := strings.TrimSpace(raw)
		if trimmed == "" {
			continue
		}
		appendTarget(scope.NormalizeTarget(trimmed))
	}

	// 任意執行類工具：批准前必須宣告目標，否則整筆決策失敗且不得寫入任何資料。
	if extension.Arbitrary && len(targets) == 0 {
		return errors.New("任意執行類工具必須先宣告本次會接觸的目標清單（scopeTargets），才能批准")
	}

	classes := []string{}
	if conditions != nil {
		for _, class := range conditions.ActionClasses {
			if trimmed := strings.TrimSpace(class); trimmed != "" {
				classes = append(classes, trimmed)
			}
		}
	}
	if len(classes) == 0 {
		classes = []string{actionClass}
	}

	owner := h.scopeOwner(conditions, &extension)

	var validUntil *time.Time
	if conditions != nil && strings.TrimSpace(conditions.ValidUntil) != "" {
		parsed, err := time.Parse(time.RFC3339, strings.TrimSpace(conditions.ValidUntil))
		if err != nil {
			return fmt.Errorf("scopeConditions.validUntil 必須是 RFC3339 時間格式: %w", err)
		}
		utc := parsed.UTC()
		validUntil = &utc
	}

	now := time.Now()
	switch decision {
	case scopeDecisionApprovePermanent:
		for _, target := range targets {
			targetType, targetValue := scopeTargetTypeValue(target)
			if err := database.UpsertScopeTarget(ctx, h.db, database.ScopeTarget{
				ID:            "scope_" + strings.ReplaceAll(uuid.New().String(), "-", ""),
				Owner:         owner,
				TargetType:    targetType,
				TargetValue:   targetValue,
				ActionClasses: classes,
				Conditions:    database.ScopeConditions{},
				ValidUntil:    validUntil,
				Provenance: database.ScopeProvenance{
					Source:       scopeProvenanceSource,
					DecidedBy:    "human",
					DecidedAt:    now,
					EvidenceHash: interruptID,
					Note:         comment,
				},
				Status:    database.ScopeTargetStatusActive,
				CreatedAt: now,
			}); err != nil {
				return err
			}
		}
	case scopeDecisionApproveOnce, scopeDecisionApproveConditional, "approve":
		maxUses := 1
		if decision == scopeDecisionApproveConditional && conditions != nil && conditions.MaxUses > 0 {
			maxUses = conditions.MaxUses
		}
		for _, target := range targets {
			targetType, targetValue := scopeTargetTypeValue(target)
			if err := database.CreateScopeGrant(ctx, h.db, database.ScopeGrant{
				ID:            "grant_" + strings.ReplaceAll(uuid.New().String(), "-", ""),
				TargetType:    targetType,
				TargetValue:   targetValue,
				ActionClasses: classes,
				MaxUses:       maxUses,
				ValidUntil:    validUntil,
				IssuedBy:      "human:" + interruptID,
				IssuedAt:      now,
				Evidence:      comment,
				Status:        database.ScopeGrantStatusActive,
			}); err != nil {
				return err
			}
		}
	case "reject":
		for _, target := range targets {
			if err := database.RecordScopeDenial(ctx, h.db, database.ScopeDenial{
				Target:    target.Key(),
				Owner:     owner,
				Reason:    "rejected",
				DecidedBy: "human",
				DecidedAt: now,
			}); err != nil {
				return err
			}
		}
	default:
		return fmt.Errorf("不支援的 scope 決策詞彙: %s", decision)
	}
	return nil
}

// resolveScopeInterrupt 處理 scope_extension 模式的決策請求。
//
// 與既有 approval／review_edit 模式的差別：
//   - 決策詞彙不同（approve_permanent／approve_once／approve_conditional／reject）。
//   - 會寫 registry（scope_targets／scope_grants／scope_denials）。
//   - 必須先寫完 registry，才把決定送回等待中的工具呼叫。
func (h *AgentHandler) resolveScopeInterrupt(ctx context.Context, interruptID, decision, comment string, conditions *hitlScopeConditions, declared []string) error {
	if h == nil || h.db == nil {
		return errors.New("hitl manager 尚未初始化")
	}
	decision = strings.ToLower(strings.TrimSpace(decision))
	switch decision {
	case scopeDecisionApprovePermanent, scopeDecisionApproveOnce, scopeDecisionApproveConditional, "approve", "reject":
	default:
		return fmt.Errorf("scope_extension 模式的決策只能是 %s／%s／%s／approve／reject",
			scopeDecisionApprovePermanent, scopeDecisionApproveOnce, scopeDecisionApproveConditional)
	}

	var mode, payloadRaw string
	err := h.db.QueryRow(`SELECT mode, COALESCE(payload, '') FROM hitl_interrupts WHERE id = ? AND status = 'pending'`, interruptID).
		Scan(&mode, &payloadRaw)
	if err != nil {
		return errors.New("interrupt not found or already resolved")
	}
	if strings.TrimSpace(mode) != scopeExtensionMode {
		return errors.New("此中斷不是 scope_extension 模式，請改用一般 HITL 決策")
	}

	var payload scopeInterruptPayload
	if err := json.Unmarshal([]byte(payloadRaw), &payload); err != nil {
		return fmt.Errorf("scope 中斷 payload 解析失敗: %w", err)
	}

	// 先驗證（fail closed）：驗證不過就不寫任何資料。
	if err := h.validateScopeDecision(&payload, decision, declared); err != nil {
		return err
	}

	if err := h.applyScopeDecision(ctx, interruptID, &payload, decision, comment, conditions, declared); err != nil {
		return err
	}

	// 寫完 registry 才把決定送回去：原地續跑時 executor 才查得到授權。
	h.hitlManager.mu.RLock()
	p, ok := h.hitlManager.pending[interruptID]
	h.hitlManager.mu.RUnlock()
	if !ok {
		return errors.New("interrupt not found or already resolved")
	}
	select {
	case p.decideCh <- hitlDecision{Decision: decision, Comment: strings.TrimSpace(comment)}:
		return nil
	default:
		return errors.New("interrupt already resolved or decision channel busy")
	}
}

// validateScopeDecision 檢查決策本身是否合法（不寫入任何資料）。
func (h *AgentHandler) validateScopeDecision(payload *scopeInterruptPayload, decision string, declared []string) error {
	if payload == nil {
		return errors.New("scope 中斷 payload 不完整")
	}
	if payload.ScopeExtension.Arbitrary && decision != "reject" {
		hasTarget := false
		for _, raw := range declared {
			if strings.TrimSpace(raw) != "" {
				hasTarget = true
				break
			}
		}
		if !hasTarget {
			return errors.New("任意執行類工具必須先宣告本次會接觸的目標清單（scopeTargets），才能批准")
		}
	}
	return nil
}

// writeScopeDenials 把逾時自動拒絕記進拒絕記憶。
func (h *AgentHandler) writeScopeDenials(ctx context.Context, extension *scopeExtensionPayload, owner, comment string) {
	if extension == nil || h.db == nil {
		return
	}
	now := time.Now()
	for _, item := range extension.Uncovered {
		target := scope.NormalizeTarget(item.Raw)
		key := target.Key()
		if key == "" {
			key = item.Key
		}
		if err := database.RecordScopeDenial(ctx, h.db, database.ScopeDenial{
			Target:    key,
			Owner:     owner,
			Reason:    "rejected",
			DecidedBy: "system",
			DecidedAt: now,
		}); err != nil && h.logger != nil {
			h.logger.Warn("寫入 scope 拒絕記憶失敗", zap.Error(err), zap.String("target", key))
		}
	}
}

// scopeOwner 推導新授權的 owner。
//
// 順序：操作者指定 → 相鄰授權的 owner → 設定檔 DefaultOwner → "adhoc"。
func (h *AgentHandler) scopeOwner(conditions *hitlScopeConditions, extension *scopeExtensionPayload) string {
	if conditions != nil {
		if owner := strings.TrimSpace(conditions.Owner); owner != "" {
			return owner
		}
	}
	if owner := h.scopeOwnerFromExtension(extension); owner != "" {
		return owner
	}
	if h.config != nil {
		if owner := strings.TrimSpace(h.config.Scope.DefaultOwner); owner != "" {
			return owner
		}
	}
	return "adhoc"
}

// scopeOwnerFromExtension 從相鄰授權取 owner（沒有相鄰就回空字串）。
func (h *AgentHandler) scopeOwnerFromExtension(extension *scopeExtensionPayload) string {
	if extension == nil {
		return ""
	}
	for _, item := range extension.Adjacent {
		if owner := strings.TrimSpace(item.Owner); owner != "" {
			return owner
		}
	}
	return ""
}

// scopeEnforcementMode 回傳目前的執行面強制模式。
func (h *AgentHandler) scopeEnforcementMode() string {
	if h == nil || h.config == nil {
		return config.ScopeEnforcementOff
	}
	return h.config.Scope.EnforcementMode()
}

// scopeService 建立 scope 判定服務（延遲建立，避免 handler 初始化順序問題）。
func (h *AgentHandler) scopeService() *scope.Service {
	if h == nil || h.db == nil {
		return nil
	}
	return scope.NewService(h.db)
}

// scopeToolConfig 找出工具設定（動作類別與參數定義）。
func (h *AgentHandler) scopeToolConfig(toolName string) *config.ToolConfig {
	if h == nil || h.config == nil {
		return nil
	}
	trimmed := strings.TrimSpace(toolName)
	for i := range h.config.Security.Tools {
		if strings.EqualFold(strings.TrimSpace(h.config.Security.Tools[i].Name), trimmed) {
			return &h.config.Security.Tools[i]
		}
	}
	return nil
}

// scopeExtensionTimeout 決定 scope 中斷的等待逾時。
//
// 優先用 scope.timeout_seconds；為 0 時沿用該會話的 HITL 逾時設定；
// 兩者都沒有就是「等操作者裁決」（與既有 HITL 的 timeout=0 語意一致）。
func (h *AgentHandler) scopeExtensionTimeout(conversationID string) time.Duration {
	if h == nil || h.config == nil {
		return 0
	}
	if h.config.Scope.TimeoutSeconds > 0 {
		return time.Duration(h.config.Scope.TimeoutSeconds) * time.Second
	}
	if h.hitlManager == nil {
		return 0
	}
	cfg, err := h.hitlManager.LoadConversationConfig(conversationID)
	if err != nil || cfg == nil || cfg.TimeoutSeconds <= 0 {
		return 0
	}
	return time.Duration(cfg.TimeoutSeconds) * time.Second
}

// scopeAdditionalArgs 取出工具呼叫的額外參數（目標可能藏在裡面的清單檔）。
func scopeAdditionalArgs(args map[string]interface{}) []string {
	if args == nil {
		return nil
	}
	raw, ok := args["additional_args"]
	if !ok || raw == nil {
		return nil
	}
	switch value := raw.(type) {
	case string:
		if strings.TrimSpace(value) == "" {
			return nil
		}
		return []string{value}
	case []string:
		return value
	case []interface{}:
		out := make([]string, 0, len(value))
		for _, item := range value {
			if text := strings.TrimSpace(fmt.Sprintf("%v", item)); text != "" {
				out = append(out, text)
			}
		}
		return out
	default:
		return nil
	}
}

// scopeTargetToItem 把 scope.Target 轉成 payload 的目標項目。
func scopeTargetToItem(target scope.Target) scopeTargetItem {
	return scopeTargetItem{
		Raw:  target.Raw,
		Host: target.Host,
		Port: target.Port,
		Kind: string(target.Kind),
		Key:  target.Key(),
		URL:  target.URL,
	}
}

// scopeTargetTypeValue 把 scope.Target 轉成 registry 的 (target_type, target_value)。
func scopeTargetTypeValue(target scope.Target) (string, string) {
	switch target.Kind {
	case scope.TargetURLPrefix:
		if target.URL != "" {
			return database.ScopeTargetTypeURLPrefix, target.URL
		}
		return database.ScopeTargetTypeHost, target.Host
	case scope.TargetCIDR:
		return database.ScopeTargetTypeCIDR, target.Host
	case scope.TargetWildcard:
		return database.ScopeTargetTypeWildcard, target.Host
	default:
		return database.ScopeTargetTypeHost, target.Host
	}
}

// scopeDeniedMessage 把拒絕結果組成給模型看的訊息。
func scopeDeniedMessage(denials []scope.Denial) string {
	parts := make([]string, 0, len(denials))
	for _, denial := range denials {
		host := denial.Target.Host
		if host == "" {
			host = denial.Target.Raw
		}
		parts = append(parts, host+"（"+denial.Reason+"："+denial.Detail+"）")
	}
	return "目標不在授權範圍內，已拒絕本次工具呼叫：" + strings.Join(parts, "；") +
		"。請勿重試同一目標，改用已授權的目標或先請操作者授權。"
}

// scopeRejectedMessage 把操作者的拒絕組成給模型看的訊息。
//
// 訊息必須明確說「已記住為拒絕，不要重試」——否則模型會一直換寫法重試同一目標。
func scopeRejectedMessage(comment string) string {
	msg := "操作者拒絕了本次目標授權；此目標已被記住為拒絕，不要重試。"
	if trimmed := strings.TrimSpace(comment); trimmed != "" {
		msg += "（操作者留言：" + trimmed + "）"
	}
	return msg
}

// recordScopeAudit 寫入 scope 判定稽核。
func (h *AgentHandler) recordScopeAudit(c *gin.Context, toolName, actionClass, mode string, covered []scope.Match, denied []scope.Denial, uncovered []scope.Target, decision, decidedBy, interruptID string) {
	if h == nil || h.audit == nil {
		return
	}
	detail := map[string]interface{}{
		"enforcement": mode,
		"actionClass": actionClass,
		"decision":    decision,
		"decidedBy":   decidedBy,
		"interruptId": interruptID,
		"covered":     scopeMatchesDetail(covered),
		"uncovered":   scopeTargetsDetail(uncovered),
		"denied":      scopeDenialsDetail(denied),
	}
	result := "success"
	message := "scope 判定完成"
	if len(uncovered) > 0 || len(denied) > 0 {
		result = "failure"
		message = "scope 判定未通過"
	}
	h.audit.Record(c, audit.Entry{
		Category:     "scope",
		Action:       "scope_resolve",
		Result:       result,
		Actor:        "system",
		ResourceType: "tool",
		ResourceID:   toolName,
		Message:      message,
		Detail:       detail,
	})
}

// scopeMatchesDetail 把命中的授權轉成稽核明細。
func scopeMatchesDetail(matches []scope.Match) []map[string]interface{} {
	out := make([]map[string]interface{}, 0, len(matches))
	for _, match := range matches {
		out = append(out, map[string]interface{}{
			"grantId":       match.GrantID,
			"source":        match.Source,
			"owner":         match.Owner,
			"host":          match.Target.Host,
			"actionClasses": match.ActionClasses,
		})
	}
	return out
}

// scopeTargetsDetail 把未覆蓋目標轉成稽核明細。
func scopeTargetsDetail(targets []scope.Target) []map[string]interface{} {
	out := make([]map[string]interface{}, 0, len(targets))
	for _, target := range targets {
		out = append(out, map[string]interface{}{
			"raw":  target.Raw,
			"host": target.Host,
			"port": target.Port,
			"kind": string(target.Kind),
			"key":  target.Key(),
		})
	}
	return out
}

// scopeDenialsDetail 把拒絕結果轉成稽核明細。
func scopeDenialsDetail(denials []scope.Denial) []map[string]interface{} {
	out := make([]map[string]interface{}, 0, len(denials))
	for _, denial := range denials {
		out = append(out, map[string]interface{}{
			"host":   denial.Target.Host,
			"reason": denial.Reason,
			"detail": denial.Detail,
		})
	}
	return out
}

// PendingInterruptMode 回傳某個中斷目前的模式（查資料庫＝權威來源）。
//
// 找不到或已裁決時回傳空字串。決策端用它分流：scope_extension 走專屬詞彙與
// 落地規則，approval／review_edit 維持既有行為（只接受 approve／reject）。
func (m *HITLManager) PendingInterruptMode(interruptID string) string {
	if m == nil || m.db == nil {
		return ""
	}
	interruptID = strings.TrimSpace(interruptID)
	if interruptID == "" {
		return ""
	}
	var mode string
	err := m.db.QueryRow(`SELECT mode FROM hitl_interrupts WHERE id = ? AND status = 'pending'`, interruptID).Scan(&mode)
	if err != nil {
		return ""
	}
	return strings.TrimSpace(mode)
}

// createScopePendingInterrupt 建立 scope_extension 的待裁決中斷。
//
// 刻意不呼叫 ensureConversationHITLModePersisted：scope_extension 是「目標授權」
// 的中斷，不是「這個會話開啟了人機協同」的開關，寫進 hitl_conversation_configs
// 會污染既有 HITL 設定（讓 refresh 後的側欄以為會話模式被改成 scope_extension）。
func (m *HITLManager) createScopePendingInterrupt(conversationID, assistantMessageID, toolName, toolCallID, payload string) (*pendingInterrupt, error) {
	if m == nil || m.db == nil {
		return nil, errors.New("hitl manager 尚未初始化")
	}
	now := time.Now()
	id := "hitl_" + strings.ReplaceAll(uuid.New().String(), "-", "")
	p := &pendingInterrupt{
		ConversationID: conversationID,
		InterruptID:    id,
		Mode:           scopeExtensionMode,
		ToolName:       toolName,
		ToolCallID:     toolCallID,
		decideCh:       make(chan hitlDecision, 1),
	}
	// 先放進記憶體待辦再寫資料庫：決策端是「看到資料庫有 pending 列」才會動作，
	// 順序反過來會有「資料庫已有列、但待辦還沒註冊」的短窗，決策會被當成找不到。
	m.mu.Lock()
	m.pending[id] = p
	m.mu.Unlock()
	if _, err := m.db.Exec(`INSERT INTO hitl_interrupts
		(id, conversation_id, message_id, mode, tool_name, tool_call_id, payload, status, reviewer, created_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 'human', ?)`,
		id, conversationID, assistantMessageID, scopeExtensionMode, toolName, toolCallID, payload, now); err != nil {
		m.mu.Lock()
		delete(m.pending, id)
		m.mu.Unlock()
		return nil, err
	}
	return p, nil
}
