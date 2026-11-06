package redirect

import (
	"strings"
	"testing"
)

func TestRewriteControlledEndpointsReplacesPayloadPositions(t *testing.T) {
	const endpoint = "https://97y.me/tjneJ"

	cases := []struct {
		name     string
		text     string
		keep     []string
		observed bool
		wantURL  string
		keepURL  string
		wantHits int
	}{
		{
			name:     "query 跳轉參數值",
			text:     "1. curl -sk 'https://victim.example/go?url=https://evil.example/steal' -o out.html",
			keep:     []string{"victim.example"},
			wantURL:  "https://evil.example/steal",
			wantHits: 1,
		},
		{
			name:     "Location 標頭值預設不改（觀測到的回應值是證據）",
			text:     "回應：HTTP 302\nLocation: https://evil.example/land\n確認跳轉。",
			keepURL:  "https://evil.example/land",
			wantHits: 0,
		},
		{
			name:     "Location 標頭值：明確要求時才改",
			text:     "回應：HTTP 302\nLocation: https://evil.example/land\n確認跳轉。",
			wantURL:  "https://evil.example/land",
			wantHits: 1,
			observed: true,
		},
		{
			name:     "JS 指派 targetUrl",
			text:     `const targetUrl = "https://gofun222.com/";`,
			wantURL:  "https://gofun222.com/",
			wantHits: 1,
		},
		{
			name:     "JSON 指派 callbackUrl",
			text:     `{"callbackUrl":"https://evil.example/cb","x":1}`,
			wantURL:  "https://evil.example/cb",
			wantHits: 1,
		},
		{
			name:     "受控端點標籤",
			text:     "受控端點：https://evil.example/cb\n目標：www.victim.example",
			keep:     []string{"victim.example"},
			wantURL:  "https://evil.example/cb",
			wantHits: 1,
		},
		{
			name:     "目標站自己的網址保留",
			text:     "curl https://vegankingcafe.com.tw/style.js -o style.js",
			keep:     []string{"vegankingcafe.com.tw"},
			wantURL:  "",
			wantHits: 0,
		},
		{
			name:     "目標站的子網域保留",
			text:     "https://www.vegankingcafe.com.tw/wp-json/ 回傳 name=金萬兩",
			keep:     []string{"vegankingcafe.com.tw"},
			wantURL:  "",
			wantHits: 0,
		},
		{
			name:     "後綴相似的網域不算同一個站",
			text:     "https://vegankingcafe.com.tw.evil.example/go?url=https://evil.example/x",
			keep:     []string{"vegankingcafe.com.tw"},
			wantURL:  "https://evil.example/x",
			wantHits: 1,
		},
		{
			name:     "非 payload 位置的網址不動",
			text:     "影響：攻擊者可讓受害者跳向第三方站 https://third.example/x 進行釣魚。",
			wantURL:  "",
			wantHits: 0,
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			out, hits, replaced := RewriteControlledEndpointsWithOptions(tc.text, RewriteOptions{
				Endpoint:        endpoint,
				KeepHosts:       tc.keep,
				IncludeObserved: tc.observed,
			})
			if hits != tc.wantHits {
				t.Fatalf("hits = %d, want %d (out=%q)", hits, tc.wantHits, out)
			}
			if tc.keepURL != "" && !strings.Contains(out, tc.keepURL) {
				t.Fatalf("該保留的網址不見了：%q", out)
			}
			if tc.wantURL == "" {
				if out != tc.text {
					t.Fatalf("文字被改動了：\n got %q\nwant %q", out, tc.text)
				}
				return
			}
			if strings.Contains(out, tc.wantURL) {
				t.Fatalf("舊網址仍留在文字裡：%q", out)
			}
			if !strings.Contains(out, endpoint) {
				t.Fatalf("受控端點沒寫進去：%q", out)
			}
			if len(replaced) != tc.wantHits {
				t.Fatalf("replaced = %v, want %d 筆", replaced, tc.wantHits)
			}
		})
	}
}

func TestRewriteControlledEndpointsIsIdempotent(t *testing.T) {
	const endpoint = "https://97y.me/tjneJ"
	text := "步驟：對目標帶入 url=https://evil.example/steal 參數，值設為受控端點。"

	once, hits, _ := RewriteControlledEndpoints(text, endpoint, nil)
	if hits != 1 {
		t.Fatalf("第一次 hits = %d, want 1", hits)
	}
	twice, hits2, _ := RewriteControlledEndpoints(once, endpoint, nil)
	if hits2 != 0 {
		t.Fatalf("第二次 hits = %d, want 0", hits2)
	}
	if once != twice {
		t.Fatalf("第二次執行改动了文字：\n once  %q\n twice %q", once, twice)
	}
}

func TestRewriteControlledEndpointsKeepsSentencePunctuation(t *testing.T) {
	const endpoint = "https://97y.me/tjneJ"
	text := "目標回應 url=https://evil.example/land，確認跳轉。"

	out, hits, _ := RewriteControlledEndpoints(text, endpoint, nil)
	if hits != 1 {
		t.Fatalf("hits = %d, want 1", hits)
	}
	if !strings.Contains(out, endpoint+"，") {
		t.Fatalf("標點被吃掉了：%q", out)
	}
}

func TestRewriteControlledEndpointsEncodesLikeOriginal(t *testing.T) {
	const endpoint = "https://97y.me/tjneJ"
	text := "https://victim.example/go?url=https%3A%2F%2Fevil.example%2Fsteal"

	out, hits, _ := RewriteControlledEndpoints(text, endpoint, nil)
	if hits != 1 {
		t.Fatalf("hits = %d, want 1", hits)
	}
	if strings.Contains(out, "evil.example") {
		t.Fatalf("舊網址仍留在文字裡：%q", out)
	}
	if !strings.Contains(out, "url=https%3A%2F%2F97y.me%2FtjneJ") {
		t.Fatalf("沒有維持原本的 percent-encoding：%q", out)
	}
}

func TestRewriteControlledEndpointsEmptyInputs(t *testing.T) {
	out, hits, replaced := RewriteControlledEndpoints("", "https://97y.me/tjneJ", nil)
	if out != "" || hits != 0 || replaced != nil {
		t.Fatalf("空文字應原樣回傳：%q %d %v", out, hits, replaced)
	}
	out, hits, _ = RewriteControlledEndpoints("https://evil.example/x", "", nil)
	if out != "https://evil.example/x" || hits != 0 {
		t.Fatalf("空端點應原樣回傳：%q %d", out, hits)
	}
}

// 目標欄位常只寫其中一個子網域，兄弟子網域仍然是同一個站 —— 不能當 payload 換掉。
func TestRewriteControlledEndpointsKeepsSiblingSubdomains(t *testing.T) {
	const endpoint = "https://97y.me/tjneJ"

	cases := []struct {
		name     string
		text     string
		site     []string
		wantHits int
	}{
		{
			name:     "同一可註冊網域的兄弟子網域保留",
			text:     "證據：returnUrl=https://www.chailease.com.tw/membership/",
			site:     []string{"uat-member-center-frontstage-service.chailease.com.tw"},
			wantHits: 0,
		},
		{
			name:     "不同可註冊網域照樣換",
			text:     "證據：returnUrl=https://evil.example/membership/",
			site:     []string{"uat-member-center-frontstage-service.chailease.com.tw"},
			wantHits: 1,
		},
		{
			name:     "後綴相似的網域不算同一個站",
			text:     "證據：returnUrl=https://chailease.com.tw.evil.example/x",
			site:     []string{"www.chailease.com.tw"},
			wantHits: 1,
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			out, hits, _ := RewriteControlledEndpointsWithOptions(tc.text, RewriteOptions{
				Endpoint:      endpoint,
				KeepSiteHosts: tc.site,
			})
			if hits != tc.wantHits {
				t.Fatalf("hits = %d, want %d (out=%q)", hits, tc.wantHits, out)
			}
			if tc.wantHits == 0 && out != tc.text {
				t.Fatalf("文字被改動了：\n got %q\nwant %q", out, tc.text)
			}
			if tc.wantHits == 1 && !strings.Contains(out, endpoint) {
				t.Fatalf("受控端點沒寫進去：%q", out)
			}
		})
	}
}

// 私有／回環／link-local 位址通常是受害者自己的內網架構，預設不改。
func TestRewriteControlledEndpointsSkipsPrivateIPs(t *testing.T) {
	const endpoint = "https://97y.me/tjneJ"

	for _, target := range []string{
		"https://10.5.0.2/",
		"http://127.0.0.1:1433/",
		"http://169.254.169.254/latest/meta-data/",
		"http://localhost:4200/",
		"http://192.168.1.1/",
	} {
		text := "環境變數 URL=" + target
		out, hits, _ := RewriteControlledEndpointsWithOptions(text, RewriteOptions{Endpoint: endpoint})
		if hits != 0 {
			t.Fatalf("私有位址 %s 被改寫了：%q", target, out)
		}
		if out != text {
			t.Fatalf("私有位址 %s 的文字被改動：%q", target, out)
		}

		out, hits, _ = RewriteControlledEndpointsWithOptions(text, RewriteOptions{
			Endpoint:        endpoint,
			AllowPrivateIPs: true,
		})
		if hits != 1 {
			t.Fatalf("AllowPrivateIPs=true 時 %s 應被改寫，hits=%d (out=%q)", target, hits, out)
		}
	}
}

// 中文紀錄的 Target 欄位常用全形括號包補充說明，不切開就會把主機名認錯。
func TestTargetHostsSplitsFullWidthPunctuation(t *testing.T) {
	hosts := TargetHosts("103.129.178.179（www.pacific-prt.com）主機級防火牆規則")
	found := map[string]bool{}
	for _, host := range hosts {
		found[host] = true
	}
	if !found["www.pacific-prt.com"] {
		t.Fatalf("全形括號沒有切開：%v", hosts)
	}
	if !found["103.129.178.179"] {
		t.Fatalf("IP 沒被取出來：%v", hosts)
	}
	for _, host := range hosts {
		if strings.ContainsAny(host, "（）") {
			t.Fatalf("主機名還帶著全形括號：%v", hosts)
		}
	}
}

// 目標欄位寫成 host:port 時，主機名本身仍必須被取出來 —— 否則目標站自己的
// 位址會被當成攻擊者的 payload 換掉。
func TestTargetHostsExtractsHostWithPort(t *testing.T) {
	hosts := TargetHosts("154.84.99.175:10943 (m.bc-galaxy.com)")
	found := map[string]bool{}
	for _, host := range hosts {
		found[host] = true
	}
	if !found["154.84.99.175"] {
		t.Fatalf("host:port 的主機名沒被取出來：%v", hosts)
	}
	if !found["m.bc-galaxy.com"] {
		t.Fatalf("括號裡的主機名沒被取出來：%v", hosts)
	}
}

// 證據裡的「证书 CN=*.alibabacorp.com」這種 key=value 形式也要認得。
func TestTargetHostsHandlesKeyValueAndWildcard(t *testing.T) {
	hosts := TargetHosts("merchant.finance.cainiao.com:443 (TLS 协商)；证书 CN=*.alibabacorp.com (GlobalSign)")
	found := map[string]bool{}
	for _, host := range hosts {
		found[host] = true
	}
	if !found["merchant.finance.cainiao.com"] {
		t.Fatalf("host:port 的主機名沒被取出來：%v", hosts)
	}
	if !found["alibabacorp.com"] {
		t.Fatalf("萬用字號主機名沒被取出來：%v", hosts)
	}
}

// 盤點與實際改寫必須用同一個保護判斷，否則數字會對不起來。
func TestProtectedHostMatchesRewriteBehaviour(t *testing.T) {
	keep := []string{"victim.example"}
	site := []string{"www.chailease.com.tw"}
	if !ProtectedHost("www.chailease.com.tw", keep, site) {
		t.Fatal("兄弟子網域應被視為同一個站")
	}
	if ProtectedHost("evil.example", keep, site) {
		t.Fatal("外部網址不該被視為同一個站")
	}
	if !PrivateHost("10.5.0.2") || !PrivateHost("localhost") {
		t.Fatal("私有位址判斷錯誤")
	}
	if PrivateHost("97y.me") {
		t.Fatal("公網網址不該被當成私有位址")
	}
}
