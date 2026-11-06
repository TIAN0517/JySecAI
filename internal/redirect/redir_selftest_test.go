package redirect

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
)

// TestEndpointSelfTest 用本地 httptest 模擬三類「受害者跳轉入口」，
// 證明：只要回應 Location 真的指向我們設定的受控端點主機，IsReflected=true；
// 相對跳轉／同域名前綴偽裝都不會被誤判成命中。payload 就是 cfg.Redirect.URLs[0]。
func TestEndpointSelfTest(t *testing.T) {
	const endpoint = "https://97y.me/tjneJ" // 原本指定的 implant/beacon 回連端點

	client := newProbeClient(nil) // 與 Probe() 相同：永不自動重導向

	mkServer := func(loc string, echoQuery bool) (*httptest.Server, func()) {
		srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if echoQuery {
				w.Header().Set("Location", r.URL.Query().Get("url")) // open-redirect: 原样回传我们灌进去的 payload host
			} else if loc != "" {
				w.Header().Set("Location", loc)                        // fixed location to emit
			} else {
				w.Header().Set("Location", "/static.html")             // 無害站内相对跳转，不含主机名 → not reflected
			}
			w.WriteHeader(http.StatusOK)
			fmt.Fprint(w, "<html></html>")
		}))
		return srv, srv.Close
	}

	type fixture struct {
		name   string
		loc    string // empty => echo ?url back; "/" static relative; other => exact literal
		echo   bool   // when true, ignore loc and reflect whatever url param we injected
		wantOK bool   // expected probe.Reflected == wantOK && status==200 && no error
	}

	fixtures := []fixture{
		{"open-redirect: victim 反射我們的端點 → confirmed", "", true, true},
		{"静态页面相对跳转 /static.html → not reflected", "/static.html", false, false},
		{"同域后缀伪装 https://evil.97y.me/x → not reflected", "https://evil.97y.me/x", false, false}, // extractHost evil.97y.me vs normalized 97y.me ≠ (精确匹配避免后缀误判)
		{"整段绝对URL指向端点 endpoint?x=1 → confirmed", endpoint + "?x=1", false, true},              // exact host match even with different path/query
	}

	ctx := context.Background()
	results := make([]bool, len(fixtures))
	for i, fx := range fixtures {
		srv, done := mkServer(fx.loc, fx.echo)
		func() {
			defer done()
			target := fmt.Sprintf("%s/go?foo=bar&url=%s+placeholder", srv.URL, srv.URL)
			res := ProbeWithMethod(ctx, client, http.MethodGet, target, "url", endpoint)

			ok := res.Status == http.StatusOK && res.Location != "" && res.Reflected == fx.wantOK && res.Error == ""
			results[i] = ok
			t.Logf("[%d/%d] %-58q status=%d location=%q reflected=%v want=%v err=%q -> %v",
				i+1, len(fixtures), fx.name, res.Status, res.Location, res.Reflected, fx.wantOK, res.Error, ok)
		}()
	}

	var passed int
	for _, r := range results { if r { passed++ } }
	if passed != len(results) {
		t.Fatalf("判定與預期不符：%d/%d 通過，請檢查 IsReflected/Probe 邏輯。results=%v", passed, len(results), results)
	}

	detected := DetectRedirectParams(endpoint) // sanity: query-less target keeps fixed order first element intact
	if len(detected) == 0 || detected[0] != defaultRedirectParams[0] {
		t.Errorf("DetectRedirectParams 順序異常: %v", detected)
	}

	fmt.Printf("\n=== controlled-endpoint self-test PASSED (%d/%d): payload host '%s' is correctly recognized as a redirect hit when the victim reflects its hostname ===\n", passed, len(results), endpoint)
}
