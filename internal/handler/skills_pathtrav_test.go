package handler

import (
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

// 這是完整走真實 gin 路由的端對端測試。skillpackage 底層的測試只能證明
// SkillDir 有驗證；這裡證明的是攻擊者真正能送出來的那個 URL 不再有效。
//
// 载荷用 %5C 而不是 %2F：gin 會把 %2F 留在路徑裡造成 404（路由不匹配），
// 所以只擋 %2F 的修補在 Windows 上完全無效 —— 這是這個漏洞的關鍵細節。

const traversalSecret = "PRIVATE-KEY-MATERIAL"

func newSkillsTraversalEnv(t *testing.T) (*gin.Engine, string) {
	t.Helper()
	gin.SetMode(gin.TestMode)

	base := t.TempDir()
	skillsRoot := filepath.Join(base, "skills")
	demo := filepath.Join(skillsRoot, "demo-skill")
	if err := os.MkdirAll(demo, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(demo, "SKILL.md"), []byte("---\nname: demo-skill\n---\nhello"), 0644); err != nil {
		t.Fatal(err)
	}
	// skillsRoot 外面的一顆「值得偷的東西」。
	if err := os.WriteFile(filepath.Join(base, "id_rsa"), []byte(traversalSecret), 0600); err != nil {
		t.Fatal(err)
	}
	// 以及一個待刪的目錄，驗證 RemoveAll 也打不出去。
	victim := filepath.Join(base, "victim-data")
	if err := os.MkdirAll(victim, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(victim, "keep.txt"), []byte("keep"), 0644); err != nil {
		t.Fatal(err)
	}

	h := NewSkillsHandler(&config.Config{SkillsDir: skillsRoot}, filepath.Join(base, "config.yaml"), zap.NewNop())

	r := gin.New()
	// 與 internal/app/app.go 的註冊方式一致。
	r.GET("/api/skills/:name/files", h.ListSkillPackageFiles)
	r.GET("/api/skills/:name/file", h.GetSkillPackageFile)
	r.PUT("/api/skills/:name/file", h.PutSkillPackageFile)
	r.PUT("/api/skills/:name", h.UpdateSkill)
	r.DELETE("/api/skills/:name", h.DeleteSkill)
	r.GET("/api/skills/:name", h.GetSkill)
	return r, base
}

// 每個 handler、每一種逃逸寫法都必須被擋下來。
func TestSkillsHandlersRejectEscapingName(t *testing.T) {
	// `..%5C` 逐層往上，數量足夠從 skills/ 回到 temp base。
	escapes := []string{
		"..%5C",
		"..%5C..%5C",
		"..%5c..%5c",
		"..%5C..%5C..%5C",
		"%2e%2e%5c%2e%2e%5c",
		"..%5Cvictim-data",
		"..%5C..%5Cvictim-data%5C..%5C",
	}
	cases := []struct{ method, path string }{
		{http.MethodGet, "/api/skills/%s/file?path=id_rsa"},
		{http.MethodGet, "/api/skills/%s/files"},
		{http.MethodGet, "/api/skills/%s?resource_path=id_rsa"},
		{http.MethodGet, "/api/skills/%s"},
		{http.MethodDelete, "/api/skills/%s"},
		{http.MethodPut, "/api/skills/%s/file"},
		{http.MethodPut, "/api/skills/%s"},
	}
	for _, tc := range cases {
		for _, esc := range escapes {
			t.Run(tc.method+" "+esc, func(t *testing.T) {
				r, _ := newSkillsTraversalEnv(t)
				w := httptest.NewRecorder()
				r.ServeHTTP(w, httptest.NewRequest(tc.method, strings.Replace(tc.path, "%s", esc, 1), nil))
				if w.Code == http.StatusOK {
					t.Errorf("status=200 for %s; body=%s", tc.path, w.Body.String())
				}
				if strings.Contains(w.Body.String(), traversalSecret) {
					t.Errorf("response leaked file content: %s", w.Body.String())
				}
			})
		}
	}
}

// 擋下來還不夠 —— 目標檔案必須真的沒被讀到 / 刪掉。
func TestSkillsTraversalDoesNotTouchFilesystem(t *testing.T) {
	r, base := newSkillsTraversalEnv(t)

	w := httptest.NewRecorder()
	r.ServeHTTP(w, httptest.NewRequest(http.MethodGet,
		"/api/skills/..%5C..%5C/file?path=id_rsa", nil))
	if strings.Contains(w.Body.String(), traversalSecret) {
		t.Fatalf("read succeeded through traversal: %s", w.Body.String())
	}

	w = httptest.NewRecorder()
	r.ServeHTTP(w, httptest.NewRequest(http.MethodDelete, "/api/skills/..%5Cvictim-data", nil))
	if _, err := os.Stat(filepath.Join(base, "victim-data", "keep.txt")); err != nil {
		t.Errorf("victim directory outside skillsRoot was removed: %v", err)
	}
}

// 修補不能等於「把功能關掉」：合法的 skill 讀取必須照常運作。
func TestSkillsHandlersStillServeLegitimateSkill(t *testing.T) {
	r, _ := newSkillsTraversalEnv(t)

	for _, tc := range []struct{ method, path, want string }{
		{http.MethodGet, "/api/skills/demo-skill/file?path=SKILL.md", "demo-skill"},
		{http.MethodGet, "/api/skills/demo-skill/files", "SKILL.md"},
		{http.MethodGet, "/api/skills/demo-skill?resource_path=SKILL.md", "demo-skill"},
	} {
		w := httptest.NewRecorder()
		r.ServeHTTP(w, httptest.NewRequest(tc.method, tc.path, nil))
		if w.Code != http.StatusOK {
			t.Errorf("%s %s: status=%d body=%s", tc.method, tc.path, w.Code, w.Body.String())
			continue
		}
		if !strings.Contains(w.Body.String(), tc.want) {
			t.Errorf("%s %s: body missing %q: %s", tc.method, tc.path, tc.want, w.Body.String())
		}
	}
}
