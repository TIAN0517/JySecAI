package robot

import (
	"errors"
	"net/url"
	"strings"
	"testing"
)

func TestSafeRobotHTTPErrorRemovesCredentialURL(t *testing.T) {
	const secret = "bot-secret-token"
	err := &url.Error{Op: "Get", URL: "https://api.example/bot" + secret + "/updates", Err: errors.New("connection refused")}
	safe := safeRobotHTTPError("telegram getUpdates", err)
	if safe == nil || strings.Contains(safe.Error(), secret) || strings.Contains(safe.Error(), "/bot") {
		t.Fatalf("credential URL leaked through error: %v", safe)
	}
	if !strings.Contains(safe.Error(), "connection refused") {
		t.Fatalf("underlying diagnostic was lost: %v", safe)
	}
}
