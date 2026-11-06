package attackchain

import (
	"testing"
)

// 這組測試守住「創建名一律為目標 DNS」。
//
// 事實名（fact_key）是跨委任延續的識別碼。用 AI 生成的標籤當 key，
// 「example.com 存在 SQL 注入」這種標籤每次措辭都不同 ——
// 事實會碎成幾十筆看起來不同、其實是同一件事的記錄，而且不同目標的 slug
// 還會互相撞名。掛上目標 DNS 後這兩種問題一起消失。

func TestAllocatePromoteFactKeyUsesTargetDNSNamespace(t *testing.T) {
	used := map[string]int{}

	target := Node{ID: "n1", Type: "target", Label: "example.com"}
	if got := allocatePromoteFactKey(target, used, "example.com"); got != "target/example.com" {
		t.Fatalf("目標節點 key = %q, want target/example.com", got)
	}

	finding := Node{ID: "n2", Type: "vulnerability", Label: "login SQL 注入"}
	got := allocatePromoteFactKey(finding, used, "example.com")
	if got != "finding/example.com-login-sql" {
		t.Fatalf("發現節點 key = %q, want finding/example.com-login-sql", got)
	}

	action := Node{ID: "n3", Type: "action", Label: "dump credentials"}
	if got := allocatePromoteFactKey(action, used, "example.com"); got != "chain/example.com-dump-credentials" {
		t.Fatalf("動作節點 key = %q, want chain/example.com-dump-credentials", got)
	}
}

// TestAllocatePromoteFactKeyDoesNotDuplicateDNS 前綴不能疊成 example.com-example.com-xxx。
func TestAllocatePromoteFactKeyDoesNotDuplicateDNS(t *testing.T) {
	used := map[string]int{}
	node := Node{ID: "n1", Type: "vulnerability", Label: "example.com api 端點 SQL 注入"}
	got := allocatePromoteFactKey(node, used, "example.com")
	if got != "finding/example.com-api-sql" {
		t.Fatalf("key = %q, want finding/example.com-api-sql（不應重複 DNS 前綴）", got)
	}
}

// TestAllocatePromoteFactKeyFallsBackWithoutDNS：拿不到 DNS 時退回舊行為，不能寫不進資料。
func TestAllocatePromoteFactKeyFallsBackWithoutDNS(t *testing.T) {
	used := map[string]int{}
	node := Node{ID: "n1", Type: "vulnerability", Label: "login SQL 注入"}
	got := allocatePromoteFactKey(node, used, "")
	if got != "finding/login-sql" {
		t.Fatalf("key = %q, want finding/login-sql", got)
	}
}

// TestAllocatePromoteFactKeyCollisionsStillDistinct：不同目標的同名 slug 必須分開。
func TestAllocatePromoteFactKeyCollisionsStillDistinct(t *testing.T) {
	usedA := map[string]int{}
	usedB := map[string]int{}
	node := Node{ID: "n1", Type: "vulnerability", Label: "login SQL 注入"}

	a := allocatePromoteFactKey(node, usedA, "a.gov.tw")
	b := allocatePromoteFactKey(node, usedB, "b.gov.tw")
	if a == b {
		t.Fatalf("不同目標產生了相同 key: %q", a)
	}
	if a != "finding/a.gov.tw-login-sql" || b != "finding/b.gov.tw-login-sql" {
		t.Fatalf("key 不符預期: %q / %q", a, b)
	}
}

// TestExtractPromoteHost 目標字串解析：URL、host:port、純主機名都要能取到 DNS。
func TestExtractPromoteHost(t *testing.T) {
	cases := map[string]string{
		"https://api.example.com:8443/path?q=1": "api.example.com",
		"http://example.com":                    "example.com",
		"example.com":                           "example.com",
		"example.com:443":                       "example.com",
		"example.com/path":                      "example.com",
		"":                                      "",
	}
	for in, want := range cases {
		if got := extractPromoteHost(in); got != want {
			t.Fatalf("extractPromoteHost(%q) = %q, want %q", in, got, want)
		}
	}
}

// TestNormalizePromoteDNS IP 與非法字串不能當 DNS。
func TestNormalizePromoteDNS(t *testing.T) {
	cases := map[string]string{
		"example.com":     "example.com",
		"EXAMPLE.com":     "example.com",
		"a.b.example.com": "a.b.example.com",
		"192.168.1.1":     "", // IP 不是 DNS
		"localhost":       "", // 沒有點，不是可穩定引用的 DNS
		"":                "",
		"bad host":        "",
	}
	for in, want := range cases {
		if got := normalizePromoteDNS(in); got != want {
			t.Fatalf("normalizePromoteDNS(%q) = %q, want %q", in, got, want)
		}
	}
}

// TestNamespaceSlugByDNS 命名空間組裝的邊界。
func TestNamespaceSlugByDNS(t *testing.T) {
	cases := []struct {
		slug, dns, want string
	}{
		{"login-sql", "example.com", "example.com-login-sql"},
		{"example.com-login-sql", "example.com", "example.com-login-sql"},
		{"example.com", "example.com", "example.com"},
		{"login-sql", "", "login-sql"},
		{"", "example.com", "example.com"},
	}
	for _, tc := range cases {
		if got := namespaceSlugByDNS(tc.slug, tc.dns); got != tc.want {
			t.Fatalf("namespaceSlugByDNS(%q,%q) = %q, want %q", tc.slug, tc.dns, got, tc.want)
		}
	}
}
