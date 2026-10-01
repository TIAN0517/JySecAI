package security

import "testing"

func TestXSSPermissionMethodMapping(t *testing.T) {
	for method, expected := range map[string]string{"GET": "xss:read", "POST": "xss:write", "PUT": "xss:write", "PATCH": "xss:write", "DELETE": "xss:delete"} {
		for _, route := range []string{"/api/xss/config", "/api/xss/payloads", "/api/xss/payloads/generate", "/api/xss/payloads/:id", "/api/xss/captures/:id/status"} {
			if got := permissionForRequest(method, route); got != expected {
				t.Fatalf("%s %s = %s", method, route, got)
			}
		}
	}
	if permissionForRequest("GET", "/api/xss-not-a-route") != "" {
		t.Fatal("prefix boundary")
	}
}
