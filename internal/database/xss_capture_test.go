package database

import (
	"path/filepath"
	"strings"
	"testing"
	"time"

	"go.uber.org/zap"
)

func TestXSSCaptureCRUDAndRBACFilter(t *testing.T) {
	db, err := NewDB(filepath.Join(t.TempDir(), "xss.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	now := time.Now()
	if _, err := db.Exec(`INSERT INTO rbac_users (id,username,display_name,password_hash,enabled,is_builtin,created_at,updated_at) VALUES ('user-a','user-a','User A','hash',1,0,?,?)`, now, now); err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(`INSERT INTO rbac_users (id,username,display_name,password_hash,enabled,is_builtin,created_at,updated_at) VALUES ('user-b','user-b','User B','hash',1,0,?,?)`, now, now); err != nil {
		t.Fatal(err)
	}

	convA, err := db.CreateConversation("xss conv", ConversationCreateMeta{})
	if err != nil {
		t.Fatal(err)
	}
	if err := db.SetResourceOwner("conversation", convA.ID, "user-a"); err != nil {
		t.Fatal(err)
	}

	// 生成并落库一段载荷。
	payload := &XSSPayload{
		ID:             "p1",
		ConversationID: convA.ID,
		Name:           "login page",
		SourceURL:      "https://target.example/login",
		Status:         "armed",
		CreatedBy:      "user-a",
	}
	payload.Script = "/*dummy*/"
	created, err := db.CreateXSSPayload(payload)
	if err != nil {
		t.Fatal(err)
	}
	if created.ID != "p1" {
		t.Fatalf("payload id = %q, want p1", created.ID)
	}
	if err := db.AssignResourceToUser("user-a", "xss_payload", created.ID); err != nil {
		t.Fatal(err)
	}

	// 记录一条收割。
	capture := &XSSCapture{
		ID:             "c1",
		PayloadID:      created.ID,
		ConversationID: convA.ID,
		Status:         "new",
		SourceURL:      "https://target.example/login",
		PageTitle:      "Login",
		UserAgent:      "Mozilla/5.0",
		ClientIP:       "203.0.113.7",
		Cookies:        []XSSCookie{{Name: "session", Value: "abc123"}},
		LocalStorage:   map[string]string{"token": "ls-token"},
		SessionStorage: map[string]string{},
	}
	capRow, err := db.CreateXSSCapture(capture)
	if err != nil {
		t.Fatal(err)
	}
	if capRow.ID != "c1" {
		t.Fatalf("capture id = %q, want c1", capRow.ID)
	}

	// user-a（会话 owner）可见载荷与收割。
	accessA := RBACListAccess{UserID: "user-a", Scope: RBACScopeOwn}
	pays, total, err := db.ListXSSPayloads(XSSListFilter{}, accessA, 0, 50)
	if err != nil {
		t.Fatal(err)
	}
	if total != 1 || len(pays) != 1 || pays[0].Name != "login page" {
		t.Fatalf("user-a payload list: total=%d pays=%#v err=%v", total, pays, err)
	}
	caps, total, err := db.ListXSSCaptures(XSSListFilter{}, accessA, 0, 50)
	if err != nil {
		t.Fatal(err)
	}
	if total != 1 || len(caps) != 1 || len(caps[0].Cookies) != 1 || caps[0].Cookies[0].Name != "session" {
		t.Fatalf("user-a capture list: total=%d caps=%#v err=%v", total, caps, err)
	}
	got, err := db.GetXSSCapture("c1")
	if err != nil || got.LocalStorage["token"] != "ls-token" {
		t.Fatalf("GetXSSCapture: got=%#v err=%v", got, err)
	}
	if !db.UserCanAccessXSS(accessA, "xss_payloads", "xss_payload", "p1") {
		t.Fatal("user-a cannot access own payload")
	}
	if !db.UserCanAccessXSS(accessA, "xss_captures", "xss_capture", "c1") {
		t.Fatal("user-a cannot access own capture")
	}

	// user-b 无共享无权可见。
	accessB := RBACListAccess{UserID: "user-b", Scope: RBACScopeOwn}
	if _, total, err := db.ListXSSPayloads(XSSListFilter{}, accessB, 0, 50); err != nil || total != 0 {
		t.Fatalf("user-b sees payloads: total=%d err=%v", total, err)
	}
	if _, total, err := db.ListXSSCaptures(XSSListFilter{}, accessB, 0, 50); err != nil || total != 0 {
		t.Fatalf("user-b sees captures: total=%d err=%v", total, err)
	}
	if db.UserCanAccessXSS(accessB, "xss_captures", "xss_capture", "c1") {
		t.Fatal("user-b can access user-a capture")
	}

	// 状态流转与删除。
	if err := db.UpdateXSSCaptureStatus("c1", "seized"); err != nil {
		t.Fatal(err)
	}
	got, err = db.GetXSSCapture("c1")
	if err != nil || got.Status != "seized" {
		t.Fatalf("after update status: got=%#v err=%v", got, err)
	}
	caps, total, err = db.ListXSSCaptures(XSSListFilter{Status: "seized"}, accessA, 0, 50)
	if err != nil || total != 1 {
		t.Fatalf("filter status=seized: total=%d err=%v", total, err)
	}
	if err := db.DeleteXSSCapture("c1"); err != nil {
		t.Fatal(err)
	}
	if _, total, err := db.ListXSSCaptures(XSSListFilter{}, accessA, 0, 50); err != nil || total != 0 {
		t.Fatalf("after delete: total=%d err=%v", total, err)
	}
	if err := db.DeleteXSSPayload("p1"); err != nil {
		t.Fatal(err)
	}
	if _, err := db.GetXSSPayload("p1"); err == nil || !strings.Contains(err.Error(), "no rows") {
		t.Fatalf("GetXSSPayload after delete err=%v", err)
	}
}

func TestXSSPayloadScriptInjectSchema(t *testing.T) {
	db, err := NewDB(filepath.Join(t.TempDir(), "xss-schema.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	now := time.Now()
	if _, err := db.Exec(`INSERT INTO rbac_users (id,username,display_name,password_hash,enabled,is_builtin,created_at,updated_at) VALUES ('user-a','user-a','User A','hash',1,0,?,?)`, now, now); err != nil {
		t.Fatal(err)
	}
	conv, err := db.CreateConversation("xss schema", ConversationCreateMeta{})
	if err != nil {
		t.Fatal(err)
	}
	if err := db.SetResourceOwner("conversation", conv.ID, "user-a"); err != nil {
		t.Fatal(err)
	}
	longScript := strings.Repeat("x", 20000)
	p, err := db.CreateXSSPayload(&XSSPayload{
		ID:             "p-schema",
		ConversationID: conv.ID,
		Name:           "schema",
		Script:         longScript,
		Status:         "armed",
		CreatedBy:      "user-a",
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(p.Script) < 20000 {
		t.Fatalf("script truncated: %d", len(p.Script))
	}
}