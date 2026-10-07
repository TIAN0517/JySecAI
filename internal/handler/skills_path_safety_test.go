package handler

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"jysecai/internal/config"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// skills 路徑逃逸防護的行為測試。
//
// 為什麼走 HTTP 層而不是只測 isValidSkillName：
// isValidSkillName 只是一個字串函式。真正的風險在「c.Param("name") 未經驗證就
// 被交給 filepath.Join / os.RemoveAll」這個組合，路由怎麼把 :name 填進去、
// 哪個 handler 忘了驗證，都只有在 HTTP 層才看得見。所以這裡註冊真實路由、
// 打真實請求，並且斷言**根目錄之外的檔案沒有被讀到、寫到或刪掉**。
//
// 兩條紅線同時成立才算通過：
//   - 穿越型 :name 一律 400
//   - 合法名稱照常可用（避免把防護做成全面禁止，那是降弱不是修護）

const skillsConfigMarker = "JY_SECMASTER_KEY: SENTINEL-MUST-NEVER-BE-READ"

// traversalNames 是會抵達 handler 的穿越型 :name。
//
// 注意：含有未編碼 "/" 的輸入（例如 "../../etc"）不會抵達 handler —— gin 的
// :name 只匹配單一路徑 segment，路由層就會 404。那類案例歸路由層管，不在此列。
//
// "..%5c..%5csecrets" 是 Windows 上最實際的攻擊面：反斜線在 URL 規格裡是合法
// 字元，編碼後可以留在單一 segment 內，而 filepath.Join 在 Windows 上會把它
// 當成目錄分隔符清理成多層穿越。
var traversalNames = []string{
	"..",
	".",
	"..%5c..%5csecrets",
	"..\\..\\secrets",
	"demo-skill\\..\\..\\secrets",
	"..%252f..%252fsecrets", // 雙重編碼，落地後仍含 %
	"C:\\Windows\\System32",
}

// newSkillsTestEnv 建立一個隔離的 config 根目錄，並回傳掛好全部 skills 路由的
// 引擎。skills 根目錄是 <base>/skills，而「受害者」檔案一律放在 base 底下、
// skills 根之外 —— 任何一次成功的逃逸都會動到它們。
func newSkillsTestEnv(t *testing.T) (*gin.Engine, string) {
	t.Helper()

	base := t.TempDir()
	skillsRoot := filepath.Join(base, "skills")
	if err := os.MkdirAll(skillsRoot, 0755); err != nil {
		t.Fatalf("建立 skills 根目錄失敗: %v", err)
	}

	// skills 根之外的敏感檔案：config.yaml 是最真實的一個，skill 讀取端點若能
	// 逃逸就會把整份設定（含金鑰）端出來。
	if err := os.WriteFile(filepath.Join(base, "config.yaml"), []byte(skillsConfigMarker), 0644); err != nil {
		t.Fatalf("建立 victim config.yaml 失敗: %v", err)
	}
	if err := os.MkdirAll(filepath.Join(base, "roles"), 0755); err != nil {
		t.Fatalf("建立 victim roles 目錄失敗: %v", err)
	}
	if err := os.WriteFile(filepath.Join(base, "roles", "admin.yaml"), []byte("role: admin\n"), 0644); err != nil {
		t.Fatalf("建立 victim role 檔失敗: %v", err)
	}

	cfg := &config.Config{SkillsDir: "skills"}
	h := NewSkillsHandler(cfg, filepath.Join(base, "config.yaml"), zap.NewNop())

	gin.SetMode(gin.TestMode)
	r := gin.New()

	// 路由與 internal/app/app.go:1406-1417 逐一對應。少註一條就等於少測一個
	// handler，所以這裡刻意照抄正式註冊清單。
	r.GET("/skills", h.GetSkills)
	r.GET("/skills/stats", h.GetSkillStats)
	r.DELETE("/skills/stats", h.ClearSkillStats)
	r.GET("/skills/:name/files", h.ListSkillPackageFiles)
	r.GET("/skills/:name/file", h.GetSkillPackageFile)
	r.PUT("/skills/:name/file", h.PutSkillPackageFile)
	r.GET("/skills/:name/bound-roles", h.GetSkillBoundRoles)
	r.POST("/skills", h.CreateSkill)
	r.PUT("/skills/:name", h.UpdateSkill)
	r.DELETE("/skills/:name", h.DeleteSkill)
	r.DELETE("/skills/:name/stats", h.ClearSkillStatsByName)
	r.GET("/skills/:name", h.GetSkill)

	return r, base
}

func doRequest(t *testing.T, r *gin.Engine, method, target, body string) *httptest.ResponseRecorder {
	t.Helper()
	var req *http.Request
	if body == "" {
		req = httptest.NewRequest(method, target, nil)
	} else {
		req = httptest.NewRequest(method, target, strings.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
	}
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	return w
}

// assertVictimsIntact 是整個測試檔最重要的一條斷言：不管回應碼是什麼，
// skills 根之外的檔案都必須原封不動。
func assertVictimsIntact(t *testing.T, base string) {
	t.Helper()

	cfgBody, err := os.ReadFile(filepath.Join(base, "config.yaml"))
	if err != nil {
		t.Fatalf("victim config.yaml 消失或不可讀（逃逸已發生）: %v", err)
	}
	if string(cfgBody) != skillsConfigMarker {
		t.Errorf("victim config.yaml 內容被改寫: %q", string(cfgBody))
	}
	if _, err := os.Stat(filepath.Join(base, "roles", "admin.yaml")); err != nil {
		t.Errorf("victim roles/admin.yaml 消失或不可讀（逃逸已發生）: %v", err)
	}
	if _, err := os.Stat(filepath.Join(base, "skills")); err != nil {
		t.Errorf("skills 根目錄消失（整棵樹被刪除）: %v", err)
	}
	if _, err := os.Stat(filepath.Join(base, "pwned.txt")); err == nil {
		t.Error("逃逸寫入的 base/pwned.txt 存在 —— 寫入端點可被利用")
	}
}

// 讀取型端點：:name 為 ".." 時，skillpackage.SkillDir 會把根目錄移到 skills 的
// 上一層，SafeRelPath 只約束 ?path= 相對於「那個已經被逃逸的根」，於是
// ?path=config.yaml 直接讀出整份設定。
func TestSkillReadEndpointsRejectTraversalName(t *testing.T) {
	cases := []struct {
		name   string
		method string
		target func(name string) string
	}{
		{"GET /skills/:name/file", http.MethodGet,
			func(n string) string { return "/skills/" + n + "/file?path=config.yaml" }},
		{"GET /skills/:name/files", http.MethodGet,
			func(n string) string { return "/skills/" + n + "/files" }},
		{"GET /skills/:name", http.MethodGet,
			func(n string) string { return "/skills/" + n }},
		{"GET /skills/:name?resource_path=../config.yaml", http.MethodGet,
			func(n string) string { return "/skills/" + n + "?resource_path=../config.yaml" }},
	}

	for _, tc := range cases {
		for _, name := range traversalNames {
			t.Run(tc.name+"|"+name, func(t *testing.T) {
				r, base := newSkillsTestEnv(t)
				w := doRequest(t, r, tc.method, tc.target(name), "")

				if w.Code != http.StatusBadRequest {
					t.Errorf("狀態碼 = %d（body: %s），預期 400", w.Code, w.Body.String())
				}
				if strings.Contains(w.Body.String(), "SENTINEL-MUST-NEVER-BE-READ") {
					t.Errorf("回應洩漏了 skills 根之外的 config.yaml: %s", w.Body.String())
				}
				if strings.Contains(w.Body.String(), "admin.yaml") {
					t.Errorf("回應列出了 skills 根之外的 roles/admin.yaml: %s", w.Body.String())
				}
				assertVictimsIntact(t, base)
			})
		}
	}
}

// 破壞性端點。:name=.. 會讓 skillDir 解析成 config 根目錄，os.RemoveAll
// 一次就抹掉 config.yaml、roles/ 與整棵 skills/。
//
// 這個測試同時釘住兩層防護的分工（由突變測試 M28/M29 實測得出）：
//
//	M28 兩層都拿掉            → 63 個子測試轉紅
//	M29 只讓 isValidSkillName 失效 → DeleteSkill 的每一個真穿越案例（含 ..）
//	                              仍被 ensureSkillPathInRoot 擋下
//
// 所以 DeleteSkill 上那兩層**不是冗餘**，任何一層都不能單獨移除。
func TestSkillDeleteEndpointRejectsTraversalName(t *testing.T) {
	// "..%252f..%252fsecrets" 是刻意留下的案例：它解碼後是含「%」的單一字串，
	// 不是穿越。第二層只管「解析後是否還在根內」，這種字串解析後仍在根內，
	// 只有第一層的名稱白名單能擋。突變測試 M29 下只有這一個案例轉紅，
	// 正好證明兩層的職責劃分如實反映在程式碼裡。
	for _, name := range traversalNames {
		t.Run(name, func(t *testing.T) {
			r, base := newSkillsTestEnv(t)
			w := doRequest(t, r, http.MethodDelete, "/skills/"+name, "")

			if w.Code != http.StatusBadRequest {
				t.Errorf("狀態碼 = %d（body: %s），預期 400", w.Code, w.Body.String())
			}
			assertVictimsIntact(t, base)
		})
	}
}

// 寫入型端點：:name=.. + {"path":"pwned.txt"} 會在 config 根寫出一個檔案。
func TestSkillWriteEndpointsRejectTraversalName(t *testing.T) {
	body := `{"path":"pwned.txt","content":"pwned"}`

	t.Run("PUT /skills/:name/file", func(t *testing.T) {
		for _, name := range traversalNames {
			t.Run(name, func(t *testing.T) {
				r, base := newSkillsTestEnv(t)
				w := doRequest(t, r, http.MethodPut, "/skills/"+name+"/file", body)

				if w.Code != http.StatusBadRequest {
					t.Errorf("狀態碼 = %d（body: %s），預期 400", w.Code, w.Body.String())
				}
				assertVictimsIntact(t, base)
			})
		}
	})

	t.Run("PUT /skills/:name", func(t *testing.T) {
		for _, name := range traversalNames {
			t.Run(name, func(t *testing.T) {
				r, base := newSkillsTestEnv(t)
				w := doRequest(t, r, http.MethodPut, "/skills/"+name,
					`{"description":"pwned","content":"pwned"}`)

				if w.Code != http.StatusBadRequest {
					t.Errorf("狀態碼 = %d（body: %s），預期 400", w.Code, w.Body.String())
				}
				assertVictimsIntact(t, base)
			})
		}
	})
}

// 其餘以 :name 為索引的端點同樣不得接受穿越型名稱。
func TestSkillRemainingNameEndpointsRejectTraversalName(t *testing.T) {
	cases := []struct {
		name   string
		method string
		target string
	}{
		{"GET /skills/:name/bound-roles", http.MethodGet, "/skills/%s/bound-roles"},
		{"DELETE /skills/:name/stats", http.MethodDelete, "/skills/%s/stats"},
	}

	for _, tc := range cases {
		for _, name := range traversalNames {
			t.Run(tc.name+"|"+name, func(t *testing.T) {
				r, base := newSkillsTestEnv(t)
				w := doRequest(t, r, tc.method, strings.Replace(tc.target, "%s", name, 1), "")

				if w.Code != http.StatusBadRequest {
					t.Errorf("狀態碼 = %d（body: %s），預期 400", w.Code, w.Body.String())
				}
				assertVictimsIntact(t, base)
			})
		}
	}
}

// 反向保護：合法名稱必須照常工作。
//
// 這一條和上面同等重要 —— 只證明「壞的被擋掉」不足以說明防護是對的，還得
// 證明「好的沒被擋掉」。把 isValidSkillName 寫得太寬或太窄，都會在這裡現形。
func TestSkillValidNamesStillWork(t *testing.T) {
	newEnvWithSkill := func(t *testing.T) (*gin.Engine, string, string) {
		t.Helper()
		r, base := newSkillsTestEnv(t)
		dir := filepath.Join(base, "skills", "demo-skill")
		if err := os.MkdirAll(dir, 0755); err != nil {
			t.Fatalf("建立測試 skill 失敗: %v", err)
		}
		md := "---\nname: demo-skill\ndescription: demo\n---\n\n# demo\n"
		if err := os.WriteFile(filepath.Join(dir, "SKILL.md"), []byte(md), 0644); err != nil {
			t.Fatalf("建立測試 SKILL.md 失敗: %v", err)
		}
		return r, base, dir
	}

	t.Run("DELETE 合法名稱會真的刪掉該 skill", func(t *testing.T) {
		r, base, dir := newEnvWithSkill(t)
		w := doRequest(t, r, http.MethodDelete, "/skills/demo-skill", "")
		if w.Code != http.StatusOK {
			t.Fatalf("狀態碼 = %d（body: %s），預期 200 —— 合法名稱被誤擋", w.Code, w.Body.String())
		}
		if _, err := os.Stat(dir); !os.IsNotExist(err) {
			t.Errorf("合法 skill 目錄未被刪除: %v", err)
		}
		assertVictimsIntact(t, base)
	})

	t.Run("PUT /skills/:name/file 合法名稱可寫入", func(t *testing.T) {
		r, base, dir := newEnvWithSkill(t)
		w := doRequest(t, r, http.MethodPut, "/skills/demo-skill/file",
			`{"path":"notes.txt","content":"hello"}`)
		if w.Code != http.StatusOK {
			t.Fatalf("狀態碼 = %d（body: %s），預期 200 —— 合法名稱被誤擋", w.Code, w.Body.String())
		}
		got, err := os.ReadFile(filepath.Join(dir, "notes.txt"))
		if err != nil {
			t.Fatalf("合法寫入未落地: %v", err)
		}
		if string(got) != "hello" {
			t.Errorf("寫入內容 = %q, want %q", string(got), "hello")
		}
		assertVictimsIntact(t, base)
	})

	t.Run("GET /skills/:name 合法名稱可讀取", func(t *testing.T) {
		r, base, _ := newEnvWithSkill(t)
		w := doRequest(t, r, http.MethodGet, "/skills/demo-skill", "")
		if w.Code != http.StatusOK {
			t.Fatalf("狀態碼 = %d（body: %s），預期 200 —— 合法名稱被誤擋", w.Code, w.Body.String())
		}
		var resp map[string]interface{}
		if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
			t.Fatalf("回應不是合法 JSON: %v（body: %s）", err, w.Body.String())
		}
		assertVictimsIntact(t, base)
	})

	t.Run("GET /skills/:name/bound-roles 合法名稱回空清單", func(t *testing.T) {
		r, base, _ := newEnvWithSkill(t)
		w := doRequest(t, r, http.MethodGet, "/skills/demo-skill/bound-roles", "")
		if w.Code != http.StatusOK {
			t.Fatalf("狀態碼 = %d（body: %s），預期 200 —— 合法名稱被誤擋", w.Code, w.Body.String())
		}
		if !strings.Contains(w.Body.String(), "demo-skill") {
			t.Errorf("回應未包含 skill 名稱: %s", w.Body.String())
		}
		assertVictimsIntact(t, base)
	})
}

// 第二層防護：即使 isValidSkillName 日後被放寬，ensureSkillPathInRoot 仍要擋下
// 逃出 skills 根的解析結果。這裡直接測該函式，因為要觸發它必須先讓名稱通過
// 第一層驗證 —— 那正是「第一層被改壞」的情境。
func TestEnsureSkillPathInRootRejectsEscape(t *testing.T) {
	// 用真實的暫存目錄而不是寫死 "C:\..." —— filepath.Join("C:", "app") 在
	// Windows 上是磁碟相對路徑 C:app 而不是 C:\app，寫死會讓這個測試的語意
	// 取決於呼叫平台。
	base := t.TempDir()
	root := filepath.Join(base, "skills")
	if err := os.MkdirAll(root, 0755); err != nil {
		t.Fatalf("建立測試根目錄失敗: %v", err)
	}

	ok := []string{
		filepath.Join(root, "demo-skill"),
		filepath.Join(root, "demo-skill", "SKILL.md"),
	}
	for _, p := range ok {
		if err := ensureSkillPathInRoot(root, p); err != nil {
			t.Errorf("ensureSkillPathInRoot(%q) = %v，應視為合法", p, err)
		}
	}

	bad := []string{
		root,                      // 根目錄本身（os.RemoveAll(root) 會清空整棵樹）
		filepath.Join(root, ".."), // 上一層 = config 根
		filepath.Join(root, "..", "config.yaml"),
		filepath.Join(root, "a", "..", "..", "roles"),
		filepath.Join(base, "roles", "admin.yaml"),
	}
	for _, p := range bad {
		if err := ensureSkillPathInRoot(root, p); err == nil {
			t.Errorf("ensureSkillPathInRoot(%q) 回傳 nil，應視為逃逸", p)
		}
	}
}
