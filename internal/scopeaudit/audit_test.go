package scopeaudit

import "testing"

// TestPlausibleHost 確認雜訊濾網抓得到真實的自由文字殘渣。
//
// 這些字串全部來自 vulnerabilities.target 欄位的真實內容；
// 如果沒有這道濾網，它們會變成幾十張垃圾授權券等著人按核准。
func TestPlausibleHost(t *testing.T) {
	valid := []string{
		"example.com",
		"www.example.com.tw",
		"member-center-oauth-service.chailease.com.tw",
		"192.168.1.1",
		"35.213.159.179",
		"2001:db8::1",
		"xn--fiqs8s.xn--fiqs8s",
		"a-b.example.co",
	}
	for _, host := range valid {
		if !PlausibleHost(host) {
			t.Errorf("應該視為有效目標：%q", host)
		}
	}

	noisy := []string{
		"",
		"https:",
		"post https:",
		"azure blob storage 存储账号 officialchailease（https:",
		"dns.chailease.com.tw (61.63.14.15 与 61.218.16.228)",
		"118.163.168.146:110,143 (mail.houseloan.tw)",
		"35.213.159.179 (lirong-tw.com",
		"localhost",
		"example",
		"http://",
		"example .com",
		"foo..com",
		"-bad.example.com",
		"bad-.example.com",
		"example.123",
	}
	for _, host := range noisy {
		if PlausibleHost(host) {
			t.Errorf("應該視為雜訊：%q", host)
		}
	}
}
