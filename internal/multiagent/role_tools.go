package multiagent

import (
	"strings"

	"jysecai/internal/agent"
)

// 子代理工具範圍的收窄（D6）。
//
// 背景：agent.getAvailableTools 以 `len(roleToolSet) > 0` 判斷是否過濾，
// **空清單代表「不限制」**。子代理若沒有宣告 role_tools、又沒有綁角色，
// 就會拿到完整工具目錄 —— 包括父代理因為角色限制而拿不到的那些。
//
// 這裡把「空 = 不限制」當成中性元素來處理：任一端為空，交集就等於另一端。
// 這是唯一正確的合成方式，否則「子代理沒宣告」會被誤判成「一個工具都不給」，
// 那是把權限模型整個關掉，屬於降弱。

// normalizeToolKeys 去掉空白項與重複項，並保留宣告順序。
func normalizeToolKeys(keys []string) []string {
	if len(keys) == 0 {
		return nil
	}
	out := make([]string, 0, len(keys))
	seen := make(map[string]bool, len(keys))
	for _, k := range keys {
		k = strings.TrimSpace(k)
		if k == "" || seen[k] {
			continue
		}
		seen[k] = true
		out = append(out, k)
	}
	return out
}

// narrowRoleTools 求父代理允許集合與子代理宣告集合的交集。
//
// 回傳的 denyAll 是這裡最容易出錯的地方：當兩端都非空卻完全沒有交集時，
// 正確結果是「子代理一個工具都不該拿到」，但把那個空清單交給
// ToolsForRole 會被解讀成「全部工具」—— 收窄反而變成全開。
// 因此呼叫端必須用 denyAll 判斷，改以空定義清單（零工具）處理。
func narrowRoleTools(parentKeys, subKeys []string) (keys []string, denyAll bool) {
	parent := normalizeToolKeys(parentKeys)
	sub := normalizeToolKeys(subKeys)

	if len(parent) == 0 {
		// 父代理沒有收窄 → 子代理的宣告就是全部。
		return sub, false
	}
	if len(sub) == 0 {
		// 子代理沒有收窄 → 不得比父代理更寬。
		return parent, false
	}

	allow := make(map[string]bool, len(parent))
	for _, k := range parent {
		allow[k] = true
	}
	out := make([]string, 0, len(sub))
	for _, k := range sub {
		if allow[k] {
			out = append(out, k)
		}
	}
	if len(out) == 0 {
		return nil, true
	}
	return out, false
}

// resolveSubAgentDefs 把上面那道決策接到 Agent.ToolsForRole 上。
//
// toolsForRole 以函式型別注入，不是為了靈活，是為了能測到「交集為空時
// 有沒有真的跳過 ToolsForRole」—— 那正是本修正最容易寫反的地方：
// 照原樣呼叫只是得到一個空清單，而空清單會被解讀成全部工具。
func resolveSubAgentDefs(
	parentKeys, subKeys []string,
	toolsForRole func([]string) []agent.Tool,
) (defs []agent.Tool, denyAll bool) {
	narrowed, denyAll := narrowRoleTools(parentKeys, subKeys)
	if denyAll {
		// 零工具。不呼叫 toolsForRole：回傳空定義清單本身就是「沒有工具」，
		// 而 ToolsFromDefinitions 對空輸入回傳空 slice 且不報錯。
		return nil, true
	}
	return toolsForRole(narrowed), false
}
