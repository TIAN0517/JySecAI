package database

import (
	"path/filepath"
	"strings"
	"testing"
	"time"

	"go.uber.org/zap"
)

func TestCreateXssCaptureIfAvailableEnforcesExpiryAndOneTime(t *testing.T) {
	db, err := NewDB(filepath.Join(t.TempDir(), "xss-callback.db"), zap.NewNop())
	if err != nil {
		t.Fatalf("NewDB: %v", err)
	}
	defer db.Close()

	token := strings.Repeat("a", 40)
	expires := time.Now().Add(time.Hour).UTC()
	payload := &XssPayload{
		Token: token, Name: "one-time", Type: "probe", Payload: "probe",
		Config: []byte("{}"), Enabled: 1, OneTime: 1, ExpiresAt: &expires,
	}
	id, err := db.CreateXssPayload(payload)
	if err != nil {
		t.Fatalf("CreateXssPayload: %v", err)
	}

	if _, accepted, err := db.CreateXssCaptureIfAvailable(id, token, "jysec_xss_canary=interaction-probe", "", "", "", "192.0.2.1", "interaction-probe"); err != nil || !accepted {
		t.Fatalf("first callback accepted=%v err=%v", accepted, err)
	}
	if _, accepted, err := db.CreateXssCaptureIfAvailable(id, token, "jysec_xss_canary=interaction-probe", "", "", "", "192.0.2.1", "interaction-probe"); err != nil || accepted {
		t.Fatalf("replay accepted=%v err=%v", accepted, err)
	}
	got, err := db.GetXssPayload(id)
	if err != nil || got.ConsumedAt == nil || got.CaptureCount != 1 {
		t.Fatalf("payload=%+v err=%v", got, err)
	}

	expired := time.Now().Add(-time.Hour).UTC()
	expiredPayload := &XssPayload{
		Token: strings.Repeat("b", 40), Name: "expired", Type: "probe", Payload: "probe",
		Config: []byte("{}"), Enabled: 1, OneTime: 1, ExpiresAt: &expired,
	}
	expiredID, err := db.CreateXssPayload(expiredPayload)
	if err != nil {
		t.Fatalf("CreateXssPayload(expired): %v", err)
	}
	if _, accepted, err := db.CreateXssCaptureIfAvailable(expiredID, expiredPayload.Token, "jysec_xss_canary=interaction-probe", "", "", "", "192.0.2.2", "interaction-probe"); err != nil || accepted {
		t.Fatalf("expired callback accepted=%v err=%v", accepted, err)
	}
}
