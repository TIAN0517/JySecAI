package audit

import "testing"

func TestSanitizeDetailRedactsNestedCredentialFamilies(t *testing.T) {
	input := map[string]interface{}{
		"safe": "visible",
		"headers": map[string]interface{}{
			"Authorization": "Bearer top-secret",
			"Set-Cookie":    "sid=secret",
		},
		"items": []interface{}{
			map[string]interface{}{"passphrase": "secret", "name": "ok"},
		},
		"webhook_signature": "signed-secret",
	}
	got := SanitizeDetail(input, 8192)
	if got["safe"] != "visible" {
		t.Fatalf("safe value changed: %+v", got)
	}
	headers := got["headers"].(map[string]interface{})
	if headers["Authorization"] != "***" || headers["Set-Cookie"] != "***" {
		t.Fatalf("headers were not redacted: %+v", headers)
	}
	items := got["items"].([]interface{})
	item := items[0].(map[string]interface{})
	if item["passphrase"] != "***" || item["name"] != "ok" {
		t.Fatalf("nested values were not sanitized precisely: %+v", item)
	}
	if got["webhook_signature"] != "***" {
		t.Fatalf("signature was not redacted: %+v", got)
	}
}
