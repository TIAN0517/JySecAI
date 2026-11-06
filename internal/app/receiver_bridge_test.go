package app

import (
	"context"
	"database/sql"
	"errors"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	_ "github.com/mattn/go-sqlite3"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/receiver"
)

// fakeSink 假的接收端，用來驗證橋接行為而不需要真的 MySQL。
type fakeSink struct {
	mu       sync.Mutex
	payloads []receiver.Payload
	fail     bool
	closed   bool
}

func (f *fakeSink) Deliver(ctx context.Context, p receiver.Payload) (receiver.DeliveryResult, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	if f.fail {
		return receiver.DeliveryResult{}, errors.New("simulated delivery failure")
	}
	f.payloads = append(f.payloads, p)
	return receiver.DeliveryResult{Delivered: true, DatasetID: "ds-" + p.SourceID}, nil
}

func (f *fakeSink) Close() error {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.closed = true
	return nil
}

func (f *fakeSink) count() int {
	f.mu.Lock()
	defer f.mu.Unlock()
	return len(f.payloads)
}

func (f *fakeSink) last() (receiver.Payload, bool) {
	f.mu.Lock()
	defer f.mu.Unlock()
	if len(f.payloads) == 0 {
		return receiver.Payload{}, false
	}
	return f.payloads[len(f.payloads)-1], true
}

// testOutbox 建一個真的本地寄件箱（暫存 SQLite）。
func testOutbox(t *testing.T) *receiver.SQLiteOutbox {
	t.Helper()
	dir := t.TempDir()
	db, err := sql.Open("sqlite3", filepath.Join(dir, "outbox.db"))
	if err != nil {
		t.Fatalf("開啟測試用 SQLite 失敗: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })
	outbox, err := receiver.NewSQLiteOutbox(db, nil)
	if err != nil {
		t.Fatalf("建立測試用寄件箱失敗: %v", err)
	}
	return outbox
}

func testBridgeConfig() config.ExternalMySQLConfig {
	return config.ExternalMySQLConfig{
		Enabled:             true,
		Host:                "127.0.0.1",
		User:                "jy_receiver",
		Database:            "jy_vuln_receiver",
		BatchSize:           50,
		PollIntervalSeconds: 1,
		TimeoutSeconds:      5,
	}
}

// waitFor 等待條件成立，最多 3 秒。
func waitFor(t *testing.T, cond func() bool) bool {
	t.Helper()
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		if cond() {
			return true
		}
		time.Sleep(10 * time.Millisecond)
	}
	return false
}

func TestVulnerabilityPayloadCarriesProvenanceAndHarvestedData(t *testing.T) {
	v := &database.Vulnerability{
		ID:              "vuln-1",
		ConversationID:  "conv-1",
		ProjectID:       "proj-1",
		Title:           "SQL injection in /api/login",
		Description:     "reproduction narrative",
		Severity:        "critical",
		Status:          "confirmed",
		Confidence:      98,
		Type:            "SQL Injection",
		Target:          "https://api.example.com/login",
		Preconditions:   "no auth",
		ReproSteps:      "curl -X POST ...",
		Evidence:        "payload: ' OR 1=1 --",
		Impact:          "full db read",
		Recommendation:  "use parameterized queries",
		RetestNotes:     "re-tested 2026-10-24",
		ConversationTag: "tag-a",
		TaskTag:         "task-a",
	}
	p := vulnerabilityPayload(v)

	if p.SourceKind != receiver.SourceKindVulnerability {
		t.Fatalf("來源類型應為 vulnerability，got %s", p.SourceKind)
	}
	if p.SourceID != "vuln-1" || p.VulnerabilityID != "vuln-1" {
		t.Fatal("來源識別與漏洞識別必須可回溯")
	}
	if p.ProjectID != "proj-1" || p.ConversationID != "conv-1" {
		t.Fatal("專案與對話溯源不可遺失")
	}
	if p.Category != "SQL Injection" || p.Severity != "critical" || p.Status != "confirmed" {
		t.Fatal("分類/嚴重度/狀態必須完整帶過去")
	}
	if p.Confidence != 98 {
		t.Fatalf("confidence 必須帶過去，got %d", p.Confidence)
	}
	if p.Evidence != v.Evidence {
		t.Fatal("證據原文必須保留")
	}
	if p.Meta == "" {
		t.Fatal("多型欄位（前置條件/影響/修補建議）必須序列化進 meta")
	}
}

func TestProjectFactPayloadCarriesHarvestedBody(t *testing.T) {
	f := &database.ProjectFact{
		ID:                     "fact-1",
		ProjectID:              "proj-1",
		FactKey:                "finding/api.example.com-sql-injection",
		Category:               "finding",
		Summary:                "SQL injection in /api/login",
		Body:                   "dumped 471 rows of users",
		Confidence:             "confirmed",
		SourceConversationID:   "conv-1",
		RelatedVulnerabilityID: "vuln-1",
	}
	p := projectFactPayload(f)

	if p.SourceKind != receiver.SourceKindProjectFact {
		t.Fatalf("來源類型應為 project_fact，got %s", p.SourceKind)
	}
	if p.FactKey != f.FactKey {
		t.Fatal("fact key 必須帶過去 —— 那是資料在平台側的命名空間")
	}
	if p.Body != f.Body {
		t.Fatal("收割到的資料本體必須完整保留")
	}
	if p.VulnerabilityID != "vuln-1" {
		t.Fatal("關聯漏洞必須帶過去")
	}
	if p.Confidence != 95 {
		t.Fatalf("confirmed 應數值化為 95，got %d", p.Confidence)
	}
	if p.Target != "api.example.com" {
		t.Fatalf("目標 DNS 應從 fact key 抽出，got %q", p.Target)
	}
}

func TestProjectFactPayloadKeepsOriginalConfidenceString(t *testing.T) {
	f := &database.ProjectFact{ID: "fact-2", FactKey: "chain/api.example.com-x", Confidence: "tentative"}
	p := projectFactPayload(f)
	if p.Confidence != 50 {
		t.Fatalf("tentative 應數值化為 50，got %d", p.Confidence)
	}
	if p.Meta == "" {
		t.Fatal("原始等級字串必須留在 meta 裡，不能只留數字")
	}
}

func TestFactConfidenceScore(t *testing.T) {
	cases := map[string]int{
		"confirmed":  95,
		"CONFIRMED":  95,
		"tentative":  50,
		"deprecated": 0,
		"":           0,
		"unknown":    0,
	}
	for in, want := range cases {
		if got := factConfidenceScore(in); got != want {
			t.Fatalf("factConfidenceScore(%q) = %d, want %d", in, got, want)
		}
	}
}

func TestExtractTargetDNS(t *testing.T) {
	cases := []struct {
		key      string
		fallback string
		want     string
	}{
		{"finding/api.example.com-sql-injection", "", "api.example.com"},
		{"target/fsm.119.gov.taipei", "", "fsm.119.gov.taipei"},
		{"chain/my-host.example.com-step", "", "my-host.example.com"},
		{"finding/api.example.com.tw-dump", "", "api.example.com.tw"},
		{"no-dns-here", "", ""},
		{"no-dns-here", "www.ithome.com.tw is the target", "www.ithome.com.tw"},
	}
	for _, c := range cases {
		if got := extractTargetDNS(c.key, c.fallback); got != c.want {
			t.Fatalf("extractTargetDNS(%q, %q) = %q, want %q", c.key, c.fallback, got, c.want)
		}
	}
}

func TestExtractTargetDNSDoesNotReturnIP(t *testing.T) {
	// IP 不是 DNS。寫進目標欄位只會讓下游以為有域名可查。
	if got := extractTargetDNS("finding/192.168.1.10-x", ""); got != "" {
		t.Fatalf("IP 不應被當成 DNS，got %q", got)
	}
}

func TestBridgeEnqueueLandsInOutboxBeforeAnyDelivery(t *testing.T) {
	// 核心紅線：收割成果落地不依賴外部 MySQL 是否連得上。
	outbox := testOutbox(t)
	sink := &fakeSink{}
	b := newReceiverBridge(outbox, testBridgeConfig(), nil)
	// 刻意不啟動排程器：外部 MySQL 還沒接上。
	b.Enqueue(receiver.Payload{SourceKind: "vulnerability", SourceID: "vuln-1", Evidence: "harvested"})

	ctx := context.Background()
	items, err := outbox.Claim(ctx, 10)
	if err != nil {
		t.Fatalf("讀取寄件箱失敗: %v", err)
	}
	if len(items) != 1 {
		t.Fatalf("成果應已落在本地寄件箱，got %d 筆", len(items))
	}
	if items[0].Payload.Evidence != "harvested" {
		t.Fatalf("收割資料本體必須完整保留，got %q", items[0].Payload.Evidence)
	}
	if sink.count() != 0 {
		t.Fatal("沒有接收端時不該送出任何東西")
	}
}

func TestBridgeDeliversThroughDrainer(t *testing.T) {
	outbox := testOutbox(t)
	sink := &fakeSink{}
	b := newReceiverBridge(outbox, testBridgeConfig(), nil)
	b.SetSink(sink)
	b.Start()
	defer b.Stop()

	b.OnVulnerabilityPersisted(&database.Vulnerability{ID: "vuln-w", Title: "t", Evidence: "e"})

	if !waitFor(t, func() bool { return sink.count() == 1 }) {
		t.Fatalf("應送出 1 筆，got %d", sink.count())
	}
	p, ok := sink.last()
	if !ok || p.SourceID != "vuln-w" {
		t.Fatal("送出的內容應與觸發的漏洞一致")
	}
	// 送出成功後必須從寄件箱移除，否則會一直重送。
	ctx := context.Background()
	if n := b.Pending(ctx); n != 0 {
		t.Fatalf("送出成功後寄件箱應清空，got %d", n)
	}
}

func TestBridgeDeliversProjectFactUpdates(t *testing.T) {
	outbox := testOutbox(t)
	sink := &fakeSink{}
	b := newReceiverBridge(outbox, testBridgeConfig(), nil)
	b.SetSink(sink)
	b.Start()
	defer b.Stop()

	b.OnProjectFactUpserted(&database.ProjectFact{ID: "fact-w", FactKey: "target/api.example.com", Body: "rows"})

	if !waitFor(t, func() bool { return sink.count() == 1 }) {
		t.Fatalf("應送出 1 筆，got %d", sink.count())
	}
	p, _ := sink.last()
	if p.SourceKind != receiver.SourceKindProjectFact {
		t.Fatalf("來源類型應為 project_fact，got %s", p.SourceKind)
	}
}

func TestBridgeKeepsPayloadInOutboxWhenDeliveryFails(t *testing.T) {
	// 外部 MySQL 送不出去時，成果必須留在寄件箱等待重試 —— 不能消失。
	outbox := testOutbox(t)
	sink := &fakeSink{fail: true}
	b := newReceiverBridge(outbox, testBridgeConfig(), nil)
	b.SetSink(sink)
	b.Start()
	defer b.Stop()

	b.Enqueue(receiver.Payload{SourceKind: "vulnerability", SourceID: "vuln-fail", Evidence: "keep me"})

	if !waitFor(t, func() bool {
		_, _, failed, _ := b.Stats()
		return failed > 0
	}) {
		_, _, failed, _ := b.Stats()
		t.Fatalf("送出失敗必須被計數（failed=%d）", failed)
	}

	ctx := context.Background()
	if n := b.Pending(ctx); n != 1 {
		t.Fatalf("送出失敗後成果應留在寄件箱，got %d", n)
	}
	items, err := outbox.Claim(ctx, 10)
	if err != nil {
		t.Fatalf("讀取寄件箱失敗: %v", err)
	}
	if len(items) != 1 || items[0].Payload.Evidence != "keep me" {
		t.Fatal("失敗後成果內容必須原封不動留在寄件箱")
	}
	if items[0].Attempts < 1 {
		t.Fatalf("失敗次數必須被記錄，got %d", items[0].Attempts)
	}
}

func TestBridgeRetainsPayloadWhenSinkMissing(t *testing.T) {
	outbox := testOutbox(t)
	b := newReceiverBridge(outbox, testBridgeConfig(), nil)
	b.Start()
	defer b.Stop()

	b.Enqueue(receiver.Payload{SourceKind: "vulnerability", SourceID: "vuln-pending"})

	ctx := context.Background()
	if n := b.Pending(ctx); n != 1 {
		t.Fatalf("接收端未連線時成果應留在寄件箱，got %d", n)
	}
}

func TestSetupExternalReceiverSkipsWhenDisabled(t *testing.T) {
	cfg := &config.Config{}
	if b := setupExternalReceiver(cfg, nil, nil); b != nil {
		t.Fatal("未啟用時不該建立接收端")
	}
}

func TestBridgeMaskErrorHidesHost(t *testing.T) {
	// 日誌是最常被外帶的載體，內網位址不該跟著跑到聊天與工單裡。
	cfg := testBridgeConfig()
	cfg.Host = "10.0.0.1"
	b := newReceiverBridge(testOutbox(t), cfg, nil)
	defer b.Stop()

	err := b.maskError(errors.New("dial tcp 10.0.0.1:3306: connect: connection refused"))
	if strings.Contains(err.Error(), "10.0.0.1") {
		t.Fatalf("主機位址必須被遮掉，got %q", err.Error())
	}
	if !strings.Contains(err.Error(), "connection refused") {
		t.Fatalf("除錯需要的部分必須保留，got %q", err.Error())
	}
}

func TestSetupExternalReceiverRequiresCompleteConfig(t *testing.T) {
	// 只有 enabled、沒有 host/user/database：這是設定寫錯，
	// 應該「不啟動」，不是「用空字串去連線」。
	cfg := &config.Config{}
	cfg.ExternalMySQL.Enabled = true
	if b := setupExternalReceiver(cfg, nil, nil); b != nil {
		t.Fatal("設定不完整時不該建立接收端")
	}
}
