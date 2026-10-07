package multiagent

import (
	"reflect"
	"testing"

	"jysecai/internal/agent"
)

// 子代理工具清單不得覆寫父代理的角色限制（D6）。
//
// 缺陷成因是 runner.go 內部的變數遮蔽：函式參數 roleTools（父代理允許集合）
// 被 `roleTools := sub.RoleTools` 蓋掉，父代理的限制從未進入子代理的工具計算。
// 而 agent.getAvailableTools 以 `len(roleToolSet) > 0` 判斷、空清單 = 全部工具，
// 於是 role_tools 留空的子代理拿到完整工具目錄，父代理被剝奪的工具它都能叫。
//
// 這個檔案只測純函式；HTTP/執行期的行為由 M31 突變測試佐證（拿掉呼叫端的
// 套用後本組測試即失去作用）。

// 正規化：空白項與重複項不應影響交集結果。
func TestNarrowRoleToolsNormalizesInput(t *testing.T) {
	cases := []struct {
		name    string
		parent  []string
		sub     []string
		want    []string
		denyAll bool
	}{
		{
			name:   "兩端皆空代表都不限制",
			parent: nil, sub: nil,
			want: nil, denyAll: false,
		},
		{
			name:   "父代理不限制時子代理的宣告就是全部",
			parent: nil, sub: []string{"ls", "cat"},
			want: []string{"ls", "cat"}, denyAll: false,
		},
		{
			name:   "子代理未宣告時不得放寬父代理的限制",
			parent: []string{"ls", "cat"}, sub: nil,
			want: []string{"ls", "cat"}, denyAll: false,
		},
		{
			name:   "交集只保留兩端都有的",
			parent: []string{"ls", "cat", "nmap"}, sub: []string{"cat", "nmap", "sqlmap"},
			want: []string{"cat", "nmap"}, denyAll: false,
		},
		{
			name:   "空白項與重複項被清掉",
			parent: []string{" ls ", "ls", "", "cat"}, sub: []string{"cat", "cat", " "},
			want: []string{"cat"}, denyAll: false,
		},
		{
			name:   "結果維持子代理宣告的順序",
			parent: []string{"a", "b", "c", "d"}, sub: []string{"d", "b", "zzz"},
			want: []string{"d", "b"}, denyAll: false,
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got, denyAll := narrowRoleTools(tc.parent, tc.sub)
			if denyAll != tc.denyAll {
				t.Errorf("denyAll = %v，預期 %v", denyAll, tc.denyAll)
			}
			if !reflect.DeepEqual(got, tc.want) {
				t.Errorf("narrowRoleTools(%q, %q) = %q，預期 %q", tc.parent, tc.sub, got, tc.want)
			}
		})
	}
}

// 核心案例：子代理宣告的工具與父代理允許的工具完全不重疊。
//
// 這一條是整個修正的關鍵，因為「空清單 = 全部工具」把錯誤方向反轉了 ——
// 如果直接把空交集交給 ToolsForRole，子代理不但沒被收窄，反而拿到完整工具目錄。
// 因此呼叫端必須靠 denyAll 判斷走「零工具」分支。
func TestNarrowRoleToolsDisjointSetsDenyAll(t *testing.T) {
	got, denyAll := narrowRoleTools(
		[]string{"ls", "cat"},
		[]string{"webshell_exec", "c2_task_create"},
	)
	if !denyAll {
		t.Fatalf("完全不重疊時 denyAll 應為 true，實際 %v（結果 %q）", denyAll, got)
	}
	if len(got) != 0 {
		t.Errorf("denyAll 時應回傳空清單，實際 %q", got)
	}
}

// 一端為空不是「無交集」，而是「該端不限制」。
//
// 這兩件事在字面上都是空清單，語意卻相反，所以必須由函式本身分清楚 ——
// 否則「子代理沒宣告工具」會被誤判成「一個工具都不給」，那是把權限模型
// 整個關掉，不是收窄。
func TestNarrowRoleToolsEmptySideMeansUnrestrictedNotDisjoint(t *testing.T) {
	for _, tc := range []struct {
		name        string
		parent, sub []string
		wantLen     int
	}{
		{"父空子有", nil, []string{"ls", "cat"}, 2},
		{"父有子空", []string{"ls", "cat"}, nil, 2},
		{"兩端都空", nil, nil, 0},
	} {
		t.Run(tc.name, func(t *testing.T) {
			got, denyAll := narrowRoleTools(tc.parent, tc.sub)
			if denyAll {
				t.Fatalf("一端為空代表該端不限制，不應視為無交集")
			}
			if len(got) != tc.wantLen {
				t.Errorf("長度 = %d，預期 %d（結果 %q）", len(got), tc.wantLen, got)
			}
		})
	}
}

// 防禦性：交集結果不得大於任一端的宣告量。
func TestNarrowRoleToolsNeverWidens(t *testing.T) {
	parent := []string{"ls", "cat", "nmap", "sqlmap"}
	sub := []string{"nmap", "sqlmap", "hydra", "nikto", "msfconsole"}
	got, denyAll := narrowRoleTools(parent, sub)
	if denyAll {
		t.Fatal("預期有交集")
	}
	for _, k := range got {
		inParent, inSub := false, false
		for _, p := range parent {
			if p == k {
				inParent = true
			}
		}
		for _, s := range sub {
			if s == k {
				inSub = true
			}
		}
		if !inParent || !inSub {
			t.Errorf("結果含 %q，但它不在父=%v 或不在子=%v 之中", k, inParent, inSub)
		}
	}
}

// 以下三條釘住「呼叫端有沒有真的把父代理的限制接上去」。
//
// 只測 narrowRoleTools 是不夠的：把 runner.go 改回原本的
// `subDefs := ag.ToolsForRole(sub.RoleKeys)`，純函式測試照樣全綠。
// 所以這裡把 ToolsForRole 以函式型別注入，觀察它實際收到的鍵。

func TestResolveSubAgentDefsPassesIntersectionToToolsForRole(t *testing.T) {
	var got []string
	called := false
	fake := func(keys []string) []agent.Tool {
		called = true
		got = keys
		return []agent.Tool{{Function: agent.FunctionDefinition{Name: "cat"}}}
	}

	_, _ = resolveSubAgentDefs(
		[]string{"ls", "cat"},            // 父代理只准這兩個
		[]string{"cat", "webshell_exec"}, // 子代理想叫這兩個
		fake)

	if !called {
		t.Fatal("ToolsForRole 未被呼叫")
	}
	if !reflect.DeepEqual(got, []string{"cat"}) {
		t.Errorf("ToolsForRole 收到 %q，預期交集 [cat] —— 子代理不得取得父代理未授權的 webshell_exec", got)
	}
}

func TestResolveSubAgentDefsNeverCallsToolsForRoleWhenDisjoint(t *testing.T) {
	called := false
	fake := func(keys []string) []agent.Tool {
		called = true
		// 模擬「空清單 = 全部工具」的真實後果。
		return []agent.Tool{
			{Function: agent.FunctionDefinition{Name: "ls"}},
			{Function: agent.FunctionDefinition{Name: "webshell_exec"}},
		}
	}

	defs, denyAll := resolveSubAgentDefs(
		[]string{"ls", "cat"},
		[]string{"webshell_exec", "c2_task_create"},
		fake)

	if called {
		t.Errorf("交集為空時仍呼叫了 ToolsForRole(keys=%v) —— 空清單會被解讀為「全部工具」，"+
			"收窄等於反轉成全開", []string(nil))
	}
	if !denyAll {
		t.Error("denyAll 應為 true")
	}
	if len(defs) != 0 {
		t.Errorf("子代理應取得零工具，實際取得 %d 個：%v", len(defs), defs)
	}
}

func TestResolveSubAgentDefsUnrestrictedParentKeepsSubList(t *testing.T) {
	var got []string
	fake := func(keys []string) []agent.Tool {
		got = keys
		return nil
	}
	_, denyAll := resolveSubAgentDefs(nil, []string{"ls", "cat"}, fake)
	if denyAll {
		t.Error("父代理未設限時不應視為無交集")
	}
	if !reflect.DeepEqual(got, []string{"ls", "cat"}) {
		t.Errorf("ToolsForRole 收到 %q，預期子代理原本的宣告", got)
	}
}
