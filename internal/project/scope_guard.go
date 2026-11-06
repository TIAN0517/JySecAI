package project

import (
	"encoding/json"
	"fmt"
	"strings"

	"jysecai/internal/toolguard"
)

// 專案測試範圍（scope_json）與攔截層的橋接。
//
// scope_json 原本只進提示層：Agent 看得到「這是授權範圍」，但沒有任何強制力。
// 這裡把同一份資料解析成 toolguard.TargetScope，讓攔截層可以用同一組規則判斷。

// projectScopePayload 解析 projects.scope_json（约定字段，可扩展）。
type projectScopePayload struct {
	Targets []string `json:"targets"`
	Exclude []string `json:"exclude"`
	Notes   string   `json:"notes"`
	// Scope 是結構化授權範圍；存在時優先於 Targets / Exclude 的自由字串解析。
	Scope *projectScopeStructured `json:"scope,omitempty"`
}

// projectScopeStructured 是 scope_json 的結構化授權範圍。
type projectScopeStructured struct {
	Allow *toolguard.Scope `json:"allow,omitempty"`
	Deny  *toolguard.Scope `json:"deny,omitempty"`
}

// ParseScopeTargets 解析 projects.scope_json 為攔截層用的專案授權範圍。
//
// 結構化欄位（scope.allow / scope.deny）優先；缺省時才自動解析 targets / exclude
// 的自由字串。自由字串中無法解讀成主機的項目（例如「n/a」）會被忽略，不讓整份
// 範圍失效 —— 提示層本來就容忍這種寫法。
//
// scope_json 不是合法 JSON 時回傳錯誤；呼叫端應視為「沒有專案範圍」，而不是
// 讓整批驗證中斷。
func ParseScopeTargets(raw string) (*toolguard.TargetScope, error) {
	trimmed := strings.TrimSpace(raw)
	if trimmed == "" {
		return nil, nil
	}
	var payload projectScopePayload
	if err := json.Unmarshal([]byte(trimmed), &payload); err != nil {
		return nil, fmt.Errorf("scope_json 不是合法 JSON: %w", err)
	}

	var allow *toolguard.Scope
	var deny *toolguard.Scope
	if payload.Scope != nil {
		allow = payload.Scope.Allow
		deny = payload.Scope.Deny
	}
	if allow == nil && len(payload.Targets) > 0 {
		parsed, err := toolguard.ParseScopeEntries(payload.Targets)
		if err != nil {
			return nil, err
		}
		allow = parsed
	}
	if deny == nil && len(payload.Exclude) > 0 {
		parsed, err := toolguard.ParseScopeEntries(payload.Exclude)
		if err != nil {
			return nil, err
		}
		deny = parsed
	}
	if allow == nil && deny == nil {
		return nil, nil
	}
	return toolguard.NewTargetScope(allow, deny)
}

// scopeEntries 把結構化 Scope 攤平成可顯示的字串清單。
//
// 顯示順序固定：精確網域 → 網域後綴 → 通配符 → CIDR，讓同一份範圍在提示層與
// 報告裡的呈現順序一致。
func scopeEntries(scope *toolguard.Scope) []string {
	if scope == nil {
		return nil
	}
	out := make([]string, 0, len(scope.Domains)+len(scope.DomainSuffixes)+len(scope.Wildcards)+len(scope.CIDRs))
	out = append(out, scope.Domains...)
	out = append(out, scope.DomainSuffixes...)
	out = append(out, scope.Wildcards...)
	out = append(out, scope.CIDRs...)
	return out
}
