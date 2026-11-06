package app

import (
	"context"
	"strings"
	"sync"

	"jysecai/internal/database"
	"jysecai/internal/mcp"
	"jysecai/internal/project"
	"jysecai/internal/toolguard"
)

// 專案授權範圍接入攔截層。
//
// 專案的測試範圍（projects.scope_json）原本只進提示層：Agent 看得到「這是授權範圍」，
// 但沒有任何強制力。這裡把同一份範圍送進 toolguard：
//
//   - targets（allow）：命中者豁免內建的 government-domains 規則。
//   - exclude（deny）：命中者一律攔截，且優先於 allow。
//
// 只作用於「綁定該專案的對話」：對話沒綁專案、查不到專案、或 scope_json 壞掉時，
// 一律回傳 nil —— 既不放寬，也不攔截。

// projectScopeResolver 把「這次呼叫屬於哪個專案」換成攔截層可用的範圍。
type projectScopeResolver struct {
	db *database.DB

	mu    sync.RWMutex
	cache map[string]cachedProjectScope
}

// cachedProjectScope 是某個專案最近一次解析結果。
type cachedProjectScope struct {
	// raw 是 scope_json 的原文；原文沒變就不必重新解析。
	raw   string
	scope *toolguard.TargetScope
}

// newProjectScopeResolver 建立專案範圍解析器。
func newProjectScopeResolver(db *database.DB) *projectScopeResolver {
	return &projectScopeResolver{db: db, cache: map[string]cachedProjectScope{}}
}

// Resolve 回傳這次呼叫所屬專案的授權範圍；不適用時回傳 nil。
func (r *projectScopeResolver) Resolve(ctx context.Context) *toolguard.TargetScope {
	if r == nil || r.db == nil {
		return nil
	}
	projectID := r.projectID(ctx)
	if projectID == "" {
		return nil
	}
	proj, err := r.db.GetProject(projectID)
	if err != nil || proj == nil {
		return nil
	}
	raw := strings.TrimSpace(proj.ScopeJSON)
	if raw == "" {
		return nil
	}

	r.mu.RLock()
	cached, ok := r.cache[projectID]
	r.mu.RUnlock()
	if ok && cached.raw == raw {
		return cached.scope
	}

	scope, err := project.ParseScopeTargets(raw)
	if err != nil {
		// scope_json 壞掉不是攔截層的責任：視為沒有範圍，並讓下一個專案範圍
		// 仍然能被解析（不讓一份壞資料拖垮整個功能）。
		scope = nil
	}
	r.mu.Lock()
	r.cache[projectID] = cachedProjectScope{raw: raw, scope: scope}
	r.mu.Unlock()
	return scope
}

// projectID 從 ctx 找出這次呼叫所屬的專案。
//
// 先看 ctx 上直接帶的專案 ID；沒有就用對話 ID 反查。查不到就回傳空字串 ——
// 對話沒綁專案是正常狀態，不該被當成任何一種授權。
func (r *projectScopeResolver) projectID(ctx context.Context) string {
	if id := strings.TrimSpace(mcp.MCPProjectIDFromContext(ctx)); id != "" {
		return id
	}
	conversationID := mcpAuthorizationConversationID(ctx)
	if conversationID == "" {
		return ""
	}
	projectID, err := r.db.GetConversationProjectID(conversationID)
	if err != nil {
		return ""
	}
	return strings.TrimSpace(projectID)
}
