package forbidden

import "testing"

// 禁區判定與 all/tools/forbidden_scope.py 必須同進同退。
// 這裡把 Python 版最容易誤殺／漏殺的條目逐條釘成斷言。

func TestReasonDetectsForbiddenDomain(t *testing.T) {
	cases := []string{
		"https://epcr.tpf.gov.tw:4004/login",
		"https://app119.tfd.gov.tw/tyfdapp",
		"https://service119.119.gov.taipei/x",
		"https://www.eocapp.gov.taipei/Account/Login?ReturnUrl=",
		"https://dmap.ncdr.nat.gov.tw/",
		"https://rescueinfo.fdkc.gov.tw/",
		"https://bear.emic.gov.tw/",
		"https://www.nfa.gov.tw/",
		"https://dc.tfd.gov.tw/",
	}
	for _, url := range cases {
		if reason := Reason("", url, "", url, ""); reason == "" {
			t.Fatalf("target %q should be forbidden", url)
		}
	}
}

func TestReasonDetectsForbiddenIP(t *testing.T) {
	cases := []string{
		"http://223.200.7.74/x",
		"http://117.56.147.98/x",
		"http://210.69.42.78/x",
		"http://123.252.43.71/",
		"http://163.29.163.35/",
		"http://210.241.54.57/",
	}
	for _, url := range cases {
		if reason := Reason("", url, "", url, ""); reason != ReasonIP {
			t.Fatalf("target %q reason = %q, want %q", url, reason, ReasonIP)
		}
	}
}

// 舊規則在網域比對裡塞裸字串 119，造成版本號／IP 末段誤殺。
// 這三個必須保留（已外部查證與消防救護無關）。
func TestReasonKeepsNonForbiddenLookalikes(t *testing.T) {
	keep := []string{
		"https://www.hr5871.chailease.com.tw/job/20.6.107.119",
		"https://merchant.finance.cainiao.com/203.119.169.43",
		"https://www.szjy188.com/szjy188/itemDetail?itemId=11923",
		"https://example.com/?id=119",
	}
	for _, url := range keep {
		if reason := Reason("", url, "", url, ""); reason != "" {
			t.Fatalf("target %q must not be forbidden, got %q", url, reason)
		}
	}
}

func TestReasonDetectsBare119Label(t *testing.T) {
	if reason := Reason("", "https://app119.example.gov.tw/x", "", "https://app119.example.gov.tw/x", ""); reason != ReasonDomain {
		t.Fatalf("reason = %q, want %q", reason, ReasonDomain)
	}
}

func TestReasonDetectsContentLevel(t *testing.T) {
	cases := []struct {
		target string
		title  string
		want   string
	}{
		// gaogui.myds.me 連網域層就命中（Python 版同樣在網域層有裸 gaogui），
		// 所以這筆是網域層而不是內容層。
		{"http://gaogui.myds.me/form", "", ReasonDomain},
		{"", "高雄市消防局第三大隊幹部輪休表", ReasonTarget},
		{"https://example.com/tyfdapp", "", ReasonTarget},
		{"https://example.com/", "緊急救護系統", ReasonTarget},
	}
	for _, tc := range cases {
		if reason := Reason("", tc.target, tc.title, tc.target, ""); reason != tc.want {
			t.Fatalf("target=%q title=%q reason = %q, want %q", tc.target, tc.title, reason, tc.want)
		}
	}
}

// gaogui 在內容層必須是獨立 token：kfbgaoguei@… 是高雄市政府 SSO 信箱帳號，不是消防系統。
func TestReasonKeepsGaoguiInsideAlnum(t *testing.T) {
	url := "https://sso.example.gov.tw/mail?account=kfbgaoguei@example.gov.tw"
	if reason := Reason("", url, "", url, ""); reason != "" {
		t.Fatalf("gaogui inside alnum must not be forbidden, got %q", reason)
	}
}

func TestFilterTargetsKeepsAllowedAndDropsForbidden(t *testing.T) {
	keep, dropped := FilterTargets([]string{
		"https://www.sps-tw.com.tw/account/login/auth/",
		"https://epcr.tpf.gov.tw:4004/login",
		"https://www.sps-tw.com.tw/account/login/auth/",
		"  ",
	})
	if len(keep) != 1 || keep[0] != "https://www.sps-tw.com.tw/account/login/auth/" {
		t.Fatalf("keep = %#v", keep)
	}
	if len(dropped) != 1 {
		t.Fatalf("dropped = %#v", dropped)
	}
}

func TestHostOf(t *testing.T) {
	if got := HostOf("https://user@Example.COM:8443/path"); got != "example.com:8443" {
		t.Fatalf("HostOf = %q", got)
	}
	if got := HostOf("not a url"); got != "" {
		t.Fatalf("HostOf = %q, want empty", got)
	}
}
