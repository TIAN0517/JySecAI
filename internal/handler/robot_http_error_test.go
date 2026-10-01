package handler

import (
	"errors"
	"net/url"
	"strings"
	"testing"
)

func TestSafeRobotOutboundErrorRemovesCredentialURL(t *testing.T) {
	const secret = "corp-secret-value"
	err := &url.Error{Op: "Get", URL: "https://example.test/token?corpsecret=" + secret, Err: errors.New("timeout")}
	safe := safeRobotOutboundError(err)
	if strings.Contains(safe, secret) || strings.Contains(safe, "corpsecret") {
		t.Fatalf("credential URL leaked through error: %q", safe)
	}
	if !strings.Contains(safe, "timeout") {
		t.Fatalf("underlying diagnostic was lost: %q", safe)
	}
}
