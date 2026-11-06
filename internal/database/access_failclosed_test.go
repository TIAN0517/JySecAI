package database

import (
	"testing"
	"time"
)

// The list-scope filters used to treat an empty user ID as "no predicate",
// so the zero value of RBACListAccess meant "unrestricted". A caller that
// forgot to check the session would silently receive every tenant's rows.
// The zero value must now mean "nothing".

func seedAccessScopeVuln(t *testing.T, db *DB, title string) *Vulnerability {
	t.Helper()
	v, err := db.CreateVulnerability(&Vulnerability{
		Title: title, Description: "seeded", Severity: "high",
		Status: VulnerabilityStatusOpen, Type: "TestType", Target: "https://" + title + ".example.test",
	})
	if err != nil {
		t.Fatalf("CreateVulnerability(%s): %v", title, err)
	}
	return v
}

func TestVulnerabilityAccessFilterFailsClosedOnEmptyUser(t *testing.T) {
	db := newTriageTestDB(t)
	seedAccessScopeVuln(t, db, "a")
	seedAccessScopeVuln(t, db, "b")

	zero := RBACListAccess{}
	list, err := db.ListVulnerabilitiesForAccess(20, 0, VulnerabilityListFilter{}, zero)
	if err != nil {
		t.Fatalf("ListVulnerabilitiesForAccess: %v", err)
	}
	if len(list) != 0 {
		t.Fatalf("zero-value access listed %d rows; the filter failed open", len(list))
	}
	count, err := db.CountVulnerabilitiesForAccess(VulnerabilityListFilter{}, zero)
	if err != nil {
		t.Fatalf("CountVulnerabilitiesForAccess: %v", err)
	}
	if count != 0 {
		t.Fatalf("zero-value access counted %d rows; the filter failed open", count)
	}

	// The unfiltered internal variants are explicitly all-scope and must
	// keep working — the fix is about the *ForAccess entry points.
	if list, err := db.ListVulnerabilities(20, 0, VulnerabilityListFilter{}); err != nil || len(list) != 2 {
		t.Fatalf("ListVulnerabilities: len=%d err=%v", len(list), err)
	}
	if count, err := db.CountVulnerabilities(VulnerabilityListFilter{}); err != nil || count != 2 {
		t.Fatalf("CountVulnerabilities: count=%d err=%v", count, err)
	}
}

func TestConversationAccessFilterFailsClosedOnEmptyUser(t *testing.T) {
	db := newTriageTestDB(t)
	if _, err := db.CreateConversation("mine", ConversationCreateMeta{}); err != nil {
		t.Fatal(err)
	}
	if _, err := db.CreateConversation("theirs", ConversationCreateMeta{}); err != nil {
		t.Fatal(err)
	}

	list, err := db.ListConversationsForAccess(20, 0, "", "", "", "", RBACScopeAssigned)
	if err != nil {
		t.Fatalf("ListConversationsForAccess: %v", err)
	}
	if len(list) != 0 {
		t.Fatalf("empty user id listed %d conversations; the filter failed open", len(list))
	}
	count, err := db.CountConversationsForAccess("", "", "", RBACScopeAssigned)
	if err != nil {
		t.Fatalf("CountConversationsForAccess: %v", err)
	}
	if count != 0 {
		t.Fatalf("empty user id counted %d conversations; the filter failed open", count)
	}
}

func TestBatchAndWebshellAccessFiltersFailClosedOnEmptyUser(t *testing.T) {
	db := newTriageTestDB(t)
	now := time.Now()
	for _, id := range []string{"q1", "q2"} {
		if _, err := db.Exec(
			`INSERT INTO batch_task_queues (id, title, role, agent_mode, schedule_mode, schedule_enabled, concurrency, status, created_at, current_index)
			 VALUES (?, ?, '', 'single', 'manual', 0, 1, 'pending', ?, 0)`, id, id, now); err != nil {
			t.Fatalf("seed batch queue %s: %v", id, err)
		}
	}
	// Sanity: all-scope must actually see the rows, otherwise the assertions
	// below would pass for the wrong reason (empty table, not empty filter).
	if all, err := db.ListBatchQueuesForAccess(20, 0, "", "", "probe", RBACScopeAll); err != nil || len(all) != 2 {
		t.Fatalf("all-scope batch list: n=%d err=%v", len(all), err)
	}
	queues, err := db.ListBatchQueuesForAccess(20, 0, "", "", "", RBACScopeAssigned)
	if err != nil {
		t.Fatalf("ListBatchQueuesForAccess: %v", err)
	}
	if len(queues) != 0 {
		t.Fatalf("empty user id listed %d batch queues; the filter failed open", len(queues))
	}

	// 直接写 SQL：这个测试库没有配置 credential cipher，
	// CreateWebshellConnection 会在加密密码时失败。
	for _, id := range []string{"w1", "w2"} {
		if _, err := db.Exec(
			`INSERT INTO webshell_connections (id, url, password, type, method, cmd_param, created_at)
			 VALUES (?, ?, '', 'php', 'post', 'cmd', ?)`, id, "https://"+id+".example.test",
			now.Format("2006-01-02 15:04:05")); err != nil {
			t.Fatalf("seed webshell %s: %v", id, err)
		}
	}
	if allws, err := db.ListWebshellConnectionsForAccess("probe", RBACScopeAll, ""); err != nil || len(allws) != 2 {
		t.Fatalf("all-scope webshell list: n=%d err=%v", len(allws), err)
	}
	conns, err := db.ListWebshellConnectionsForAccess("", RBACScopeAssigned, "")
	if err != nil {
		t.Fatalf("ListWebshellConnectionsForAccess: %v", err)
	}
	if len(conns) != 0 {
		t.Fatalf("empty user id listed %d webshell connections; the filter failed open", len(conns))
	}
}

// GetModelTokenUsageStats used to accept a zero-value filter and return a
// plausible-looking all-zero summary, which reads as "you used no tokens"
// rather than "we could not tell who you are".
func TestGetModelTokenUsageStatsRejectsMissingIdentity(t *testing.T) {
	db := newTriageTestDB(t)
	if _, err := db.GetModelTokenUsageStats(ModelTokenUsageFilter{}); err == nil {
		t.Fatal("GetModelTokenUsageStats accepted a filter with no caller identity")
	}
	if _, err := db.GetModelTokenUsageStats(ModelTokenUsageFilter{
		Access: RBACListAccess{Scope: RBACScopeAll},
	}); err != nil {
		t.Fatalf("all-scope filter was rejected: %v", err)
	}
}
