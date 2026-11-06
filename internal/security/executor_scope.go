package security

import (
	"context"
	"fmt"
	"strings"
	"sync"
	"time"

	"jysecai/internal/config"
	"jysecai/internal/scope"

	"go.uber.org/zap"
)

// Scope 執行面兜底（攔截點 B）。
//
// 為什麼需要第二道
// ----------------
// handler 層的 scope gate（攔截點 A）涵蓋所有「從 Eino 工具中介層進來」的呼叫，
// 但平台還有其他路徑可以叫到工具（內部呼叫、其他 handler、批次佇列）。
// 這裡在 executor 組好 argv、真的要 spawn 之前再驗一次，任何未被授權的目標
// 都在這裡 fail closed。
//
// 為什麼用可注入的方式
// --------------------
// NewExecutor 的既有呼叫點（測試、其他組裝處）不能被破壞，所以檢查器用
// SetScopeGuard 注入；沒注入就完全不做檢查（維持既有行為）。

// ScopeGuard 是執行面的授權檢查器。
type ScopeGuard interface {
	// CheckToolScope 回傳 nil 代表允許執行；非 nil 代表拒絕（fail closed）。
	CheckToolScope(ctx context.Context, toolName, actionClass string, params []config.ParameterConfig, args map[string]interface{}) error
	// ConsumeScopeGrant 扣掉一張用掉的授權券（工具執行成功後呼叫）。
	ConsumeScopeGrant(ctx context.Context, grantID string) error
}

// RegistryScopeGuard 是以 scope registry 為依據的執行面檢查器。
type RegistryScopeGuard struct {
	service *scope.Service
	mode    string
	logger  *zap.Logger
}

// NewRegistryScopeGuard 建立 registry 檢查器。
//
// mode 是 config.Scope.EnforcementMode() 的結果：off 完全不檢查、
// audit 只記錄不阻擋、enforce 未覆蓋就拒絕。
func NewRegistryScopeGuard(service *scope.Service, mode string, logger *zap.Logger) *RegistryScopeGuard {
	return &RegistryScopeGuard{service: service, mode: mode, logger: logger}
}

// Mode 回傳這個檢查器的強制模式。
func (g *RegistryScopeGuard) Mode() string {
	if g == nil {
		return config.ScopeEnforcementOff
	}
	return g.mode
}

// CheckToolScope 判定這次工具呼叫是否被授權涵蓋。
//
// 判定順序：
//  1. off → 完全跳過。
//  2. local_analysis／offline_replay → 不碰網路，不需要 scope 檢查。
//  3. 抽出目標 → scope.Resolve；命中拒絕或未覆蓋 → 拒絕（fail closed）。
//  4. 抽不出目標（任意執行類）→ 退化成「有沒有針對這個動作類別的明確授權」。
func (g *RegistryScopeGuard) CheckToolScope(ctx context.Context, toolName, actionClass string, params []config.ParameterConfig, args map[string]interface{}) error {
	if g == nil || g.service == nil {
		return nil
	}
	mode := g.Mode()
	if mode == config.ScopeEnforcementOff {
		return nil
	}
	actionClass = strings.TrimSpace(actionClass)
	if actionClass == "" {
		actionClass = scope.ActionArbitrary
	}
	// 本機檔案分析／離線重放不碰網路，不需要授權檢查。
	if actionClass == scope.ActionLocalAnalysis || actionClass == scope.ActionOfflineReplay {
		return nil
	}

	targets, arbitrary, err := scope.ExtractTargets(toolName, params, args, scopeAdditionalArgs(args), "")
	if err != nil {
		return g.reject(mode, toolName, actionClass, "無法解析本次工具呼叫會接觸的目標："+err.Error())
	}

	if arbitrary {
		// 任意執行類工具沒有可驗證的目標，只能退化成類別授權檢查。
		// 沒有明確授權就拒絕（fail closed）：寧可多問一次，也不要放行未知目標。
		authorized, err := g.service.HasActionClassAuthorization(ctx, actionClass)
		if err != nil {
			return g.reject(mode, toolName, actionClass, "scope registry 查詢失敗："+err.Error())
		}
		if !authorized {
			return g.reject(mode, toolName, actionClass,
				"這是任意執行類工具（動作類別 "+actionClass+"），registry 內沒有針對此類別的明確授權")
		}
		return nil
	}

	result, err := g.service.Resolve(ctx, targets, actionClass, time.Now())
	if err != nil {
		return g.reject(mode, toolName, actionClass, "scope registry 查詢失敗："+err.Error())
	}
	if len(result.Denied) > 0 {
		reasons := make([]string, 0, len(result.Denied))
		for _, denial := range result.Denied {
			host := denial.Target.Host
			if host == "" {
				host = denial.Target.Raw
			}
			reasons = append(reasons, host+"（"+denial.Reason+"："+denial.Detail+"）")
		}
		return g.reject(mode, toolName, actionClass, "目標不在授權範圍內："+strings.Join(reasons, "；"))
	}
	if len(result.Uncovered) > 0 {
		hosts := make([]string, 0, len(result.Uncovered))
		for _, target := range result.Uncovered {
			hosts = append(hosts, target.Host)
		}
		return g.reject(mode, toolName, actionClass, "目標未被任何 scope 涵蓋："+strings.Join(hosts, "；"))
	}

	// 記下這次用到的授權券：工具執行成功後才扣次數。
	if state := scopeStateFromContext(ctx); state != nil {
		for _, match := range result.Covered {
			if match.Source == scope.SourceScopeGrant {
				state.addGrant(match.GrantID)
			}
		}
	}
	return nil
}

// ConsumeScopeGrant 扣掉一張用掉的授權券。
func (g *RegistryScopeGuard) ConsumeScopeGrant(ctx context.Context, grantID string) error {
	if g == nil || g.service == nil {
		return nil
	}
	return g.service.ConsumeGrant(ctx, grantID)
}

// reject 依 enforcement 模式決定拒絕或只記錄。
func (g *RegistryScopeGuard) reject(mode, toolName, actionClass, detail string) error {
	if mode == config.ScopeEnforcementAudit {
		if g.logger != nil {
			g.logger.Warn("scope 檢查未通過（audit 模式不阻擋）",
				zap.String("toolName", toolName),
				zap.String("actionClass", actionClass),
				zap.String("detail", detail),
			)
		}
		return nil
	}
	if g.logger != nil {
		g.logger.Warn("scope 檢查未通過，已拒絕執行",
			zap.String("toolName", toolName),
			zap.String("actionClass", actionClass),
			zap.String("detail", detail),
		)
	}
	return &ScopeNotCoveredError{ToolName: toolName, ActionClass: actionClass, Detail: detail}
}

// ScopeNotCoveredError 是「目標未被授權涵蓋」的錯誤（executor 層 fail closed）。
type ScopeNotCoveredError struct {
	ToolName    string
	ActionClass string
	Detail      string
}

func (e *ScopeNotCoveredError) Error() string {
	if e == nil {
		return "scope_not_covered"
	}
	return "scope_not_covered: " + e.Detail
}

// scopeCallState 是單次工具呼叫的 scope 狀態。
//
// 由 Executor 建立後放進 ctx 傳給 guard：guard 只負責「記下用到哪張券」，
// 真正扣次數由 Executor 在工具執行成功後觸發（避免失敗的呼叫也扣次數）。
type scopeCallState struct {
	mu       sync.Mutex
	grantIDs []string
}

type scopeCallStateKey struct{}

func newScopeCallState(ctx context.Context) (context.Context, *scopeCallState) {
	state := &scopeCallState{}
	return context.WithValue(ctx, scopeCallStateKey{}, state), state
}

func scopeStateFromContext(ctx context.Context) *scopeCallState {
	if ctx == nil {
		return nil
	}
	if state, ok := ctx.Value(scopeCallStateKey{}).(*scopeCallState); ok {
		return state
	}
	return nil
}

func (s *scopeCallState) addGrant(id string) {
	if s == nil || strings.TrimSpace(id) == "" {
		return
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, existing := range s.grantIDs {
		if existing == id {
			return
		}
	}
	s.grantIDs = append(s.grantIDs, id)
}

func (s *scopeCallState) grants() []string {
	if s == nil {
		return nil
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	return append([]string(nil), s.grantIDs...)
}

// checkToolScope 執行面兜底檢查（攔截點 B）。
//
// 沒注入 guard 就完全跳過（維持既有行為）；有注入就 fail closed：
// 檢查器本身出錯也視為不通過。
func (e *Executor) checkToolScope(ctx context.Context, toolName string, toolConfig *config.ToolConfig, args map[string]interface{}) error {
	if e == nil || e.scopeGuard == nil {
		return nil
	}
	actionClass := ""
	var params []config.ParameterConfig
	if toolConfig != nil {
		actionClass = strings.TrimSpace(toolConfig.ActionClass)
		params = toolConfig.Parameters
	}
	return e.scopeGuard.CheckToolScope(ctx, toolName, actionClass, params, args)
}

// commitToolScope 在工具執行成功後扣掉用掉的授權券。
//
// 失敗只記錄不報錯：工具已經執行完成，這時扣次數失敗不應該讓呼叫變成錯誤
// （那會讓模型誤以為工具失敗而重試，反而多用一次券）。
func (e *Executor) commitToolScope(ctx context.Context, state *scopeCallState) {
	if e == nil || e.scopeGuard == nil || state == nil {
		return
	}
	for _, grantID := range state.grants() {
		if err := e.scopeGuard.ConsumeScopeGrant(ctx, grantID); err != nil && e.logger != nil {
			e.logger.Warn("扣減授權券次數失敗",
				zap.String("grantId", grantID),
				zap.Error(err),
			)
		}
	}
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
