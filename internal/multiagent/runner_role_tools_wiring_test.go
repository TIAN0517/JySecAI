package multiagent

import (
	"go/ast"
	"go/parser"
	"go/token"
	"testing"
)

// 釘住 RunDeepAgent 內部的**接線**，而不只是 narrowRoleTools 的純邏輯。
//
// 為什麼需要這個檔案：把 runner.go 改回
//
//	subDefs := ag.ToolsForRole(sub.RoleTools)
//
// （也就是 D6 原本的樣子）時，subagent_role_tools_test.go 的每一條都還是綠的
// —— 因為那些測試直接呼叫 resolveSubAgentDefs，從來沒有走過 runner.go。
// 突變測試 M31 實測確認了這個盲點。純函式測試證明不了接線。
//
// 所以這裡改用 go/parser 檢查原始碼結構，沿用本 repo 既有的做法
// （internal/security/route_inventory_test.go 也是這樣守住 app.go 的路由接線）。

func parseRunner(t *testing.T) (*token.FileSet, *ast.FuncDecl) {
	t.Helper()
	fset := token.NewFileSet()
	file, err := parser.ParseFile(fset, "runner.go", nil, 0)
	if err != nil {
		t.Fatalf("解析 runner.go 失敗: %v", err)
	}
	for _, d := range file.Decls {
		if fd, ok := d.(*ast.FuncDecl); ok && fd.Name.Name == "RunDeepAgent" {
			return fset, fd
		}
	}
	t.Fatal("runner.go 中找不到 RunDeepAgent")
	return nil, nil
}

// 核心：resolveSubAgentDefs 的第一個引數必須是父代理的 roleTools 參數。
func TestRunDeepAgentPassesParentRoleToolsToSubAgentResolution(t *testing.T) {
	fset, runFn := parseRunner(t)

	calls := 0
	ast.Inspect(runFn.Body, func(n ast.Node) bool {
		call, ok := n.(*ast.CallExpr)
		if !ok {
			return true
		}
		sel, ok := call.Fun.(*ast.Ident)
		if !ok || sel.Name != "resolveSubAgentDefs" {
			return true
		}
		calls++
		if len(call.Args) == 0 {
			t.Errorf("行 %d：resolveSubAgentDefs 沒有引數", fset.Position(call.Pos()).Line)
			return true
		}
		first, ok := call.Args[0].(*ast.Ident)
		if !ok || first.Name != "roleTools" {
			t.Errorf("行 %d：resolveSubAgentDefs 的第一個引數必須是父代理的 roleTools，"+
				"實際型別 %T —— 這正是 D6 的漏洞本身：子代理因此看不到父代理的角色限制",
				fset.Position(call.Args[0].Pos()).Line, call.Args[0])
		}
		return true
	})

	if calls == 0 {
		t.Fatal("RunDeepAgent 未呼叫 resolveSubAgentDefs —— 子代理的工具範圍未受父代理約束")
	}
}

// 原始缺陷的成因是變數遮蔽：函式參數 roleTools 被 `roleTools := sub.RoleTools`
// 蓋掉。這一條直接擋那個寫法。
func TestRunDeepAgentDoesNotShadowParentRoleTools(t *testing.T) {
	fset, runFn := parseRunner(t)

	// 參數本身宣告在 runFn.Type，不在 Body 裡，所以只掃 Body 不會誤判。
	ast.Inspect(runFn.Body, func(n ast.Node) bool {
		switch node := n.(type) {
		case *ast.AssignStmt:
			for _, lhs := range node.Lhs {
				if id, ok := lhs.(*ast.Ident); ok && id.Name == "roleTools" {
					t.Errorf("行 %d：RunDeepAgent 內部重新賦值 roleTools，會遮蔽父代理允許集合。"+
						"請改用 subRoleKeys 之類的不同名稱",
						fset.Position(id.Pos()).Line)
				}
			}
		case *ast.DeclStmt:
			gd, ok := node.Decl.(*ast.GenDecl)
			if !ok || gd.Tok != token.VAR {
				return true
			}
			for _, spec := range gd.Specs {
				vs, ok := spec.(*ast.ValueSpec)
				if !ok {
					continue
				}
				for _, name := range vs.Names {
					if name.Name == "roleTools" {
						t.Errorf("行 %d：RunDeepAgent 內部宣告了區域變數 roleTools，會遮蔽父代理允許集合",
							fset.Position(name.Pos()).Line)
					}
				}
			}
		}
		return true
	})
}

// 防禦性：整個 repo 內不得再有第二個 `roleTools := sub...` 的遮蔽寫法。
// 內部 multiagent 套件日後新增迴圈時若複製了這個樣子，這一條會擋下來。
func TestNoOtherSubAgentRoleToolsShadowing(t *testing.T) {
	fset := token.NewFileSet()
	file, err := parser.ParseFile(fset, "runner.go", nil, 0)
	if err != nil {
		t.Fatalf("解析 runner.go 失敗: %v", err)
	}
	ast.Inspect(file, func(n ast.Node) bool {
		assign, ok := n.(*ast.AssignStmt)
		if !ok || assign.Tok != token.DEFINE {
			return true
		}
		// 抓 `roleTools := <expr>` 且 expr 提到 sub
		for _, lhs := range assign.Lhs {
			id, ok := lhs.(*ast.Ident)
			if !ok || id.Name != "roleTools" {
				continue
			}
			t.Errorf("行 %d：出現 `roleTools := ...` 的遮蔽賦值", fset.Position(id.Pos()).Line)
		}
		return true
	})
}
