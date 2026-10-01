package c2

import (
	"os"
	"strings"
	"testing"
)

func TestBeaconTemplateDoesNotDisableTLSVerificationByDefault(t *testing.T) {
	data, err := os.ReadFile("payload_templates/beacon.go.tmpl")
	if err != nil {
		t.Fatal(err)
	}
	templateText := string(data)
	if strings.Contains(templateText, "InsecureSkipVerify: true") {
		t.Fatal("beacon template must not hard-code disabled TLS verification")
	}
	if !strings.Contains(templateText, "InsecureSkipVerify: {{.TLSInsecureSkipVerify}}") || !strings.Contains(templateText, "MinVersion: tls.VersionTLS12") {
		t.Fatal("beacon template must use the explicit compatibility flag and TLS 1.2+")
	}
	if (&ListenerConfig{}).TLSInsecureSkipVerify {
		t.Fatal("TLS verification compatibility flag must default to false")
	}
}
