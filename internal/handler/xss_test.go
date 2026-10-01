package handler

import (
	"bytes"
	"context"
	"encoding/json"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go.uber.org/zap"
	"io"
	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/security"
	"jysecai/internal/xsshook"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func xssTestDB(t *testing.T) *database.DB {
	t.Helper()
	db, err := database.NewDB(filepath.Join(t.TempDir(), "xss.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	return db
}
func xssTestRouter(db *database.DB, cfg config.XssConfig, session security.Session) *gin.Engine {
	r := gin.New()
	group := r.Group("/api/xss", func(c *gin.Context) { c.Set(security.ContextSessionKey, session); c.Next() }, security.RBACMiddleware(db))
	RegisterXSSRoutes(group, NewXssHandler(db, &cfg, zap.NewNop()))
	return r
}
func xssRequest(r http.Handler, method, path, body string) *httptest.ResponseRecorder {
	req := httptest.NewRequest(method, path, strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	return w
}
func xssSession(user string) security.Session {
	return security.Session{UserID: user, Scope: database.RBACScopeAll, Permissions: map[string]bool{"xss:read": true, "xss:write": true, "xss:delete": true}, PermissionScopes: map[string]string{"xss:read": "all", "xss:write": "own", "xss:delete": "assigned"}}
}

func TestXSSGenerateOwnerBeforeInsertAndRichRouteContract(t *testing.T) {
	db := xssTestDB(t)
	r := xssTestRouter(db, config.XssConfig{Enabled: true, BindHost: "127.0.0.1", BindPort: 18877}, xssSession("u1"))
	w := xssRequest(r, "POST", "/api/xss/payloads/generate", `{"name":"phase1a1-test","source_url":"http://127.0.0.1/test"}`)
	if w.Code != 200 {
		t.Fatal(w.Code, w.Body.String())
	}
	var data struct {
		Payload   database.XSSPayload `json:"payload"`
		BeaconURL string              `json:"beacon_url"`
	}
	if err := json.Unmarshal(w.Body.Bytes(), &data); err != nil {
		t.Fatal(err)
	}
	if _, err := uuid.Parse(data.Payload.ID); err != nil {
		t.Fatal(err)
	}
	p, err := db.GetXSSPayload(data.Payload.ID)
	if err != nil {
		t.Fatal(err)
	}
	if p.OwnerUserID != "u1" || p.CreatedBy != "u1" || len(p.CallbackToken) != 64 || p.Enabled != 1 {
		t.Fatal("ownership/token not inserted")
	}
	if data.BeaconURL != "http://127.0.0.1:18877/api/xss/capture" || !strings.Contains(p.Script, p.CallbackToken) {
		t.Fatal("script binding/fallback")
	}
	if w = xssRequest(r, "POST", "/api/xss/payloads", `{}`); w.Code != 404 {
		t.Fatal("conflicting integer route exists")
	}
	if w = xssRequest(r, "GET", "/api/xss/config", ""); strings.Contains(w.Body.String(), p.CallbackToken) {
		t.Fatal("token in config")
	}
	p2, _ := db.CreateXSSPayload(&database.XSSPayload{OwnerUserID: "u2", Script: "synthetic"})
	if w = xssRequest(r, "DELETE", "/api/xss/payloads/"+p2.ID, ""); w.Code != 403 {
		t.Fatal("global read widened delete scope")
	}
	if w = xssRequest(r, "POST", "/api/xss/payloads/generate", `{"domain_only":true,"domain":"https://example.com"}`); w.Code != 400 {
		t.Fatal("invalid domain")
	}
}
func TestXSSManagementPermissionAndOwnList(t *testing.T) {
	db := xssTestDB(t)
	mine, _ := db.CreateXSSPayload(&database.XSSPayload{OwnerUserID: "u1", Script: "synthetic"})
	other, _ := db.CreateXSSPayload(&database.XSSPayload{OwnerUserID: "u2", Script: "synthetic"})
	s := xssSession("u1")
	s.PermissionScopes["xss:read"] = "own"
	r := xssTestRouter(db, config.XssConfig{}, s)
	w := xssRequest(r, "GET", "/api/xss/payloads", "")
	if w.Code != 200 || !strings.Contains(w.Body.String(), mine.ID) || strings.Contains(w.Body.String(), other.ID) {
		t.Fatal("list scope")
	}
	if w = xssRequest(r, "GET", "/api/xss/payloads/"+other.ID, ""); w.Code != 403 {
		t.Fatal("cross-user detail")
	}
	s.Permissions = map[string]bool{}
	r = xssTestRouter(db, config.XssConfig{}, s)
	if w = xssRequest(r, "GET", "/api/xss/config", ""); w.Code != 403 {
		t.Fatal("missing permission")
	}
}
func TestXSSGenerateParentScopeAndMismatch(t *testing.T) {
	db := xssTestDB(t)
	project, _ := db.CreateProject(&database.Project{Name: "parent"})
	conv, _ := db.CreateConversation("child", database.ConversationCreateMeta{ProjectID: project.ID})
	db.SetResourceOwner("project", project.ID, "u1")
	r := xssTestRouter(db, config.XssConfig{Enabled: true}, xssSession("u1"))
	body, _ := json.Marshal(map[string]string{"conversation_id": conv.ID, "project_id": project.ID})
	if w := xssRequest(r, "POST", "/api/xss/payloads/generate", string(body)); w.Code != 200 {
		t.Fatal("parent access", w.Code)
	}
	body, _ = json.Marshal(map[string]string{"conversation_id": conv.ID, "project_id": "other"})
	if w := xssRequest(r, "POST", "/api/xss/payloads/generate", string(body)); w.Code != 400 {
		t.Fatal("parent mismatch", w.Code)
	}
	r = xssTestRouter(db, config.XssConfig{Enabled: true}, xssSession("u2"))
	body, _ = json.Marshal(map[string]string{"conversation_id": conv.ID})
	if w := xssRequest(r, "POST", "/api/xss/payloads/generate", string(body)); w.Code != 403 {
		t.Fatal("foreign parent allowed")
	}
}
func TestXSSAuthenticatedLocalE2E(t *testing.T) {
	db := xssTestDB(t)
	auth := security.NewAuthManager(1)
	password, err := auth.AttachRBACStore(db)
	if err != nil {
		t.Fatal(err)
	}
	token, _, err := auth.Authenticate("admin", password)
	if err != nil {
		t.Fatal(err)
	}
	r := gin.New()
	server := httptest.NewUnstartedServer(r)
	base := "http://" + server.Listener.Addr().String()
	cfg := config.XssConfig{Enabled: true, PublicURL: base, CooldownSeconds: 1}
	collector := xsshook.NewCollector(db, cfg, zap.NewNop())
	r.POST("/api/xss/capture", gin.WrapH(collector))
	r.OPTIONS("/api/xss/capture", gin.WrapH(collector))
	group := r.Group("/api/xss", security.AuthMiddleware(auth), security.RBACMiddleware(db))
	RegisterXSSRoutes(group, NewXssHandler(db, &cfg, zap.NewNop()))
	// Serve the real HTML contract and production JS, with a synthetic authenticated
	// API helper. No normal app/scanner/agent startup and no external requests.
	index, err := os.ReadFile("../../web/templates/index.html")
	if err != nil {
		t.Fatal(err)
	}
	r.GET("/xss.js", func(c *gin.Context) { c.File("../../web/static/js/xss.js") })
	r.GET("/router.js", func(c *gin.Context) { c.File("../../web/static/js/router.js") })
	r.GET("/browser", func(c *gin.Context) {
		html := string(index)
		// Isolate the exact page subtree with balanced div tags in browser DOM; inert
		// template parsing avoids running any unrelated page scripts.
		indexJSON, _ := json.Marshal(html)
		tokenJSON, _ := json.Marshal(token)
		c.Header("Content-Type", "text/html; charset=utf-8")
		c.String(200, `<!doctype html><meta charset="utf-8"><div id="fixture"></div><script>const template=document.createElement('template');template.innerHTML=`+string(indexJSON)+`;document.getElementById('fixture').appendChild(template.content.querySelector('#page-xss'));window.apiFetch=(url,opts={})=>fetch(url,{...opts,headers:{...opts.headers,Authorization:'Bearer '+`+string(tokenJSON)+`}});window.applyRBACToUI=()=>{};window.confirm=()=>true;</script><script src="/xss.js"></script><script src="/router.js"></script>`)
	})
	server.Start()
	defer server.Close()
	send := func(method, path string, body []byte, authenticate bool) *http.Response {
		t.Helper()
		req, _ := http.NewRequest(method, base+path, bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		if authenticate {
			req.Header.Set("Authorization", "Bearer "+token)
		}
		resp, err := server.Client().Do(req)
		if err != nil {
			t.Fatal(err)
		}
		return resp
	}
	unauth := send("GET", "/api/xss/payloads", nil, false)
	unauth.Body.Close()
	if unauth.StatusCode != 401 {
		t.Fatal("unauthenticated management accepted")
	}
	resp := send("POST", "/api/xss/payloads/generate", []byte(`{"name":"phase1a1-test","source_url":"http://127.0.0.1/test"}`), true)
	var created struct {
		Payload database.XSSPayload `json:"payload"`
	}
	err = json.NewDecoder(resp.Body).Decode(&created)
	resp.Body.Close()
	if err != nil || resp.StatusCode != 200 {
		t.Fatal("generate", err, resp.StatusCode)
	}
	p, err := db.GetXSSPayload(created.Payload.ID)
	if err != nil {
		t.Fatal(err)
	}
	req := xsshook.CaptureRequest{PayloadID: p.ID, SourceURL: "http://127.0.0.1/test", Cookies: []xsshook.Cookie{{Name: "jysec_test", Value: "1"}}, PageTitle: `<img src=x onerror="window.__xss=1">`, UserAgent: `"><svg onload="window.__xss=2">`, LocalStorage: map[string]string{"<script>window.__xss=3</script>": "synthetic"}}
	data, _ := json.Marshal(req)
	httpReq, _ := http.NewRequest("POST", base+"/api/xss/capture", bytes.NewReader(data))
	httpReq.Header.Set("X-XSS-Token", p.CallbackToken)
	resp, err = server.Client().Do(httpReq)
	if err != nil {
		t.Fatal(err)
	}
	resp.Body.Close()
	if resp.StatusCode != 204 {
		t.Fatal("callback", resp.StatusCode)
	}
	resp = send("GET", "/api/xss/captures", nil, true)
	var listed struct {
		Captures []database.XSSCapture `json:"captures"`
	}
	err = json.NewDecoder(resp.Body).Decode(&listed)
	resp.Body.Close()
	if err != nil || len(listed.Captures) != 1 || listed.Captures[0].Cookies[0].Value != "1" {
		t.Fatal("rich capture/API", err)
	}
	malicious := `<img src=x onerror="window.__xss=4"><script>window.__xss=5</script>"><svg onload="window.__xss=6">`
	if _, err = db.Exec(`UPDATE xss_payloads SET name=?,source_url=?,status=? WHERE id=?`, malicious, malicious, malicious, p.ID); err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec(`UPDATE xss_captures SET client_ip=?,status=? WHERE id=?`, malicious, malicious, listed.Captures[0].ID); err != nil {
		t.Fatal(err)
	}
	// Browser check is opt-in only for hosts with an existing Chromium/Node toolchain.
	if os.Getenv("XSS_BROWSER_E2E") == "1" {
		ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
		defer cancel()
		cmd := exec.CommandContext(ctx, "node", "../../internal/handler/testdata/xss_browser.cjs", base, listed.Captures[0].ID)
		output, err := cmd.CombinedOutput()
		if err != nil {
			t.Fatalf("browser E2E: %v: %s", err, output)
		}
		if !strings.Contains(string(output), "BROWSER_E2E_PASS") {
			t.Fatal("browser missing success")
		}
		t.Log(string(output))
	}
	resp = send("PUT", "/api/xss/captures/"+listed.Captures[0].ID+"/status", []byte(`{"status":"analyzed"}`), true)
	io.Copy(io.Discard, resp.Body)
	resp.Body.Close()
	if resp.StatusCode != 200 {
		t.Fatal("status", resp.StatusCode)
	}
}
