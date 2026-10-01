package handler

import (
	"crypto/tls"
	"testing"

	"go.uber.org/zap"
)

func TestWebShellTLSSecureByDefault(t *testing.T) {
	t.Setenv("JYSSECAI_WEBSHELL_INSECURE", "")
	t.Setenv("JYSSECAI_WEBSHELL_CA_FILE", "")
	tr := newWebShellTransport(zap.NewNop())
	if tr.TLSClientConfig == nil || tr.TLSClientConfig.InsecureSkipVerify {
		t.Fatal("TLS certificate verification must be enabled by default")
	}
	if tr.TLSClientConfig.MinVersion < tls.VersionTLS12 {
		t.Fatalf("minimum TLS version = %d", tr.TLSClientConfig.MinVersion)
	}
}

func TestWebShellTLSInsecureCompatibilityRequiresOptIn(t *testing.T) {
	t.Setenv("JYSSECAI_WEBSHELL_INSECURE", "true")
	tr := newWebShellTransport(zap.NewNop())
	if tr.TLSClientConfig == nil || !tr.TLSClientConfig.InsecureSkipVerify {
		t.Fatal("explicit compatibility switch should allow legacy self-signed targets")
	}
}

func TestWebShellInvalidCAFailsSecurely(t *testing.T) {
	t.Setenv("JYSSECAI_WEBSHELL_INSECURE", "")
	t.Setenv("JYSSECAI_WEBSHELL_CA_FILE", "/definitely/not/a/ca.pem")
	tr := newWebShellTransport(zap.NewNop())
	if tr.TLSClientConfig == nil || tr.TLSClientConfig.InsecureSkipVerify {
		t.Fatal("invalid custom CA must not disable certificate verification")
	}
}
