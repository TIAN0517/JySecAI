package vulnmask

import (
	"strings"
	"testing"
	"unicode/utf8"
)

func TestMaskHidesPublicIPButKeepsItCorrelatable(t *testing.T) {
	policy := DefaultPolicy()
	got := policy.Mask("目標 https://118.163.168.146/events 回應 200")
	if strings.Contains(got, "118.163.168.146") {
		t.Fatalf("公網位址沒有被遮蔽: %s", got)
	}
	if !strings.Contains(got, "ip-") {
		t.Fatalf("公網位址應換成穩定代號: %s", got)
	}
	// 同一個位址必須永遠對應同一個代號，否則關聯分析會失效。
	again := policy.Mask("另一處 118.163.168.146")
	if extractPseudonym(got, "ip-") != extractPseudonym(again, "ip-") {
		t.Fatalf("同一個位址的代號不穩定: %s vs %s", got, again)
	}
}

// extractPseudonym 取出文字中的穩定代號（前綴 + 8 碼十六進位）。
func extractPseudonym(text, prefix string) string {
	index := strings.Index(text, prefix)
	if index < 0 {
		return ""
	}
	end := index + len(prefix) + 8
	if end > len(text) {
		return text[index:]
	}
	return text[index:end]
}

func TestMaskCollapsesPrivateAndLoopbackAddresses(t *testing.T) {
	policy := DefaultPolicy()
	for _, value := range []string{"10.0.0.1", "127.0.0.1", "192.168.1.1", "172.16.5.4", "169.254.169.254", "0.0.0.0"} {
		got := policy.Mask("連線 " + value + " 成功")
		if strings.Contains(got, value) {
			t.Errorf("私有/回環位址 %s 未被遮蔽: %s", value, got)
		}
		if !strings.Contains(got, InternalRedacted) {
			t.Errorf("私有/回環位址 %s 應歸為 %s: %s", value, InternalRedacted, got)
		}
	}
}

func TestMaskRedactsConfiguredIPsWithoutPseudonym(t *testing.T) {
	policy := DefaultPolicy().WithRedactedIPs("52.128.238.210")
	got := policy.Mask("平台出口 52.128.238.210")
	if strings.Contains(got, "52.128.238.210") || strings.Contains(got, "ip-") {
		t.Fatalf("指定抹除的位址不該留下代號: %s", got)
	}
	if !strings.Contains(got, InternalRedacted) {
		t.Fatalf("指定抹除的位址應歸為 %s: %s", InternalRedacted, got)
	}
}

func TestMaskHidesCredentialsInURLAndText(t *testing.T) {
	policy := DefaultPolicy()
	got := policy.Mask("GET /api?token=abc123def&user=bob password: Sup3rSecret")
	if strings.Contains(got, "abc123def") {
		t.Fatalf("URL 參數裡的 token 未被遮蔽: %s", got)
	}
	if strings.Contains(got, "Sup3rSecret") {
		t.Fatalf("本文中的密碼未被遮蔽: %s", got)
	}
	if !strings.Contains(got, RedactedSecret) {
		t.Fatalf("憑證應換成 %s: %s", RedactedSecret, got)
	}
}

func TestMaskKeepsHostnamesByDefaultAndCanHideThem(t *testing.T) {
	policy := DefaultPolicy()
	got := policy.Mask("目標 https://member-center-oauth-service.chailease.com.tw/Account/TokenEncode")
	if !strings.Contains(got, "member-center-oauth-service.chailease.com.tw") {
		t.Fatalf("預設應保留主機名: %s", got)
	}
	policy.MaskHosts = true
	hidden := policy.Mask("目標 https://member-center-oauth-service.chailease.com.tw/Account/TokenEncode")
	if strings.Contains(hidden, "chailease.com.tw") {
		t.Fatalf("開啟遮蔽主機名後仍看得到: %s", hidden)
	}
	if !strings.Contains(hidden, "host-") {
		t.Fatalf("主機名應換成穩定代號: %s", hidden)
	}
}

func TestMaskDisabledPolicyKeepsEverything(t *testing.T) {
	policy := DefaultPolicy()
	policy.MaskIPs = false
	policy.MaskSecrets = false
	got := policy.Mask("10.0.0.1 token=abc")
	if !strings.Contains(got, "10.0.0.1") || !strings.Contains(got, "abc") {
		t.Fatalf("關閉遮蔽後應保留原文: %s", got)
	}
}

// TestMaskRepairsInvalidUTF8 擋住非法位元組一路送到 MySQL。
//
// 生產資料庫的證據欄位有截斷的多位元組字元；utf8mb4 會以 Error 1366 拒收。
func TestMaskRepairsInvalidUTF8(t *testing.T) {
	policy := DefaultPolicy()
	broken := "片段 " + string([]byte{0xE6, 0x8E}) + " 結尾"
	got := policy.Mask(broken)
	if !utf8.ValidString(got) {
		t.Fatalf("遮蔽後仍是非法 UTF-8: %q", got)
	}
	if !strings.Contains(got, "片段") {
		t.Fatalf("合法片段不該被破壞: %q", got)
	}
}
