package robot

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"

	"jysecai/internal/config"

	"go.uber.org/zap"
)

// fakeOffsetStore 记录游标读写的内存实现。
type fakeOffsetStore struct {
	mu     sync.Mutex
	offset int64
	saved  []int64
}

func (f *fakeOffsetStore) GetRobotStreamOffset(string) (int64, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.offset, nil
}

func (f *fakeOffsetStore) SaveRobotStreamOffset(_ string, offset int64) error {
	f.mu.Lock()
	defer f.mu.Unlock()
	if offset > f.offset {
		f.offset = offset
	}
	f.saved = append(f.saved, offset)
	return nil
}

func (f *fakeOffsetStore) current() int64 {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.offset
}

// fakeMessageHandler 记录机器人收到的消息并回一句固定内容。
type fakeMessageHandler struct {
	mu       sync.Mutex
	received []string
}

func (f *fakeMessageHandler) HandleMessage(_, _, text string) string {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.received = append(f.received, text)
	return "ok"
}

func (f *fakeMessageHandler) all() []string {
	f.mu.Lock()
	defer f.mu.Unlock()
	return append([]string(nil), f.received...)
}

func waitFor(t *testing.T, timeout time.Duration, cond func() bool) bool {
	t.Helper()
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		if cond() {
			return true
		}
		time.Sleep(10 * time.Millisecond)
	}
	return cond()
}

func TestTelegramGetUpdatesURLCarriesOffsetSemantics(t *testing.T) {
	base := telegramGetUpdatesURL("TOKEN", 0)
	if strings.Contains(base, "offset=") {
		t.Fatalf("offset=0 must not be sent to Telegram: %s", base)
	}
	if got := telegramGetUpdatesURL("TOKEN", 42); !strings.Contains(got, "offset=42") {
		t.Fatalf("offset=42 missing in %s", got)
	}
	if got := telegramGetUpdatesURL("TOKEN", -1); !strings.Contains(got, "offset=-1") {
		t.Fatalf("offset=-1 missing in %s", got)
	}
	if got := telegramLatestUpdateURL("TOKEN"); !strings.Contains(got, "offset=-1") || !strings.Contains(got, "timeout=0") {
		t.Fatalf("latest update probe url is wrong: %s", got)
	}
}

func TestResolveTelegramStartOffsetPrefersPersistedValue(t *testing.T) {
	logger := zap.NewNop()

	// 无任何游标 -> -1（表示跳过历史积压）
	if got := resolveTelegramStartOffset(config.RobotTelegramConfig{}, nil, logger); got != -1 {
		t.Fatalf("expected -1 without any offset, got %d", got)
	}

	// 只有配置游标
	if got := resolveTelegramStartOffset(config.RobotTelegramConfig{UpdateOffset: 12}, nil, logger); got != 12 {
		t.Fatalf("expected config offset 12, got %d", got)
	}

	// 持久化游标优先
	store := &fakeOffsetStore{offset: 300}
	if got := resolveTelegramStartOffset(config.RobotTelegramConfig{}, store, logger); got != 300 {
		t.Fatalf("expected persisted offset 300, got %d", got)
	}

	// 两者都存在时取较大值，游标不回退
	store = &fakeOffsetStore{offset: 300}
	if got := resolveTelegramStartOffset(config.RobotTelegramConfig{UpdateOffset: 500}, store, logger); got != 500 {
		t.Fatalf("expected max offset 500, got %d", got)
	}
	store = &fakeOffsetStore{offset: 700}
	if got := resolveTelegramStartOffset(config.RobotTelegramConfig{UpdateOffset: 500}, store, logger); got != 700 {
		t.Fatalf("expected max offset 700, got %d", got)
	}
}

// newFakeTelegramServer 模拟 Telegram Bot API。
// offset=-1 -> 返回一条历史积压消息（update_id 100）
// offset=101 -> 返回一条新消息（update_id 101）
// offset=500 -> 返回一条新消息（update_id 501）
func newFakeTelegramServer(t *testing.T, queries *[]string, sent *[]string, mu *sync.Mutex) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasSuffix(r.URL.Path, "/sendMessage") {
			body, _ := io.ReadAll(r.Body)
			mu.Lock()
			*sent = append(*sent, string(body))
			mu.Unlock()
			w.Header().Set("Content-Type", "application/json")
			_, _ = w.Write([]byte(`{"ok":true}`))
			return
		}
		mu.Lock()
		*queries = append(*queries, r.URL.RawQuery)
		mu.Unlock()

		message := func(updateID int, text string) string {
			payload := map[string]interface{}{
				"ok": true,
				"result": []map[string]interface{}{{
					"update_id": updateID,
					"message": map[string]interface{}{
						"message_id": updateID,
						"chat":       map[string]interface{}{"id": 7, "type": "private"},
						"from":       map[string]interface{}{"id": 9, "is_bot": false},
						"text":       text,
					},
				}},
			}
			raw, _ := json.Marshal(payload)
			return string(raw)
		}

		switch r.URL.Query().Get("offset") {
		case "-1":
			w.Header().Set("Content-Type", "application/json")
			_, _ = w.Write([]byte(message(100, "历史积压消息")))
		case "101":
			w.Header().Set("Content-Type", "application/json")
			_, _ = w.Write([]byte(message(101, "新訊息")))
		case "500":
			w.Header().Set("Content-Type", "application/json")
			_, _ = w.Write([]byte(message(501, "重啟後新訊息")))
		default:
			// 模拟长轮询：没有新消息时稍作等待，避免测试里空转。
			select {
			case <-r.Context().Done():
				return
			case <-time.After(50 * time.Millisecond):
			}
			w.Header().Set("Content-Type", "application/json")
			_, _ = w.Write([]byte(`{"ok":true,"result":[]}`))
		}
	}))
	t.Cleanup(srv.Close)
	return srv
}

func TestTelegramPollSkipsBacklogAndPersistsOffset(t *testing.T) {
	var mu sync.Mutex
	var queries []string
	var sent []string
	srv := newFakeTelegramServer(t, &queries, &sent, &mu)

	oldBase := telegramAPIBase
	telegramAPIBase = srv.URL
	defer func() { telegramAPIBase = oldBase }()

	store := &fakeOffsetStore{}
	handler := &fakeMessageHandler{}
	cfg := config.RobotsConfig{Telegram: config.RobotTelegramConfig{
		Enabled:     true,
		BotToken:    "TOKEN",
		BotUsername: "scanbot",
	}}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go StartTelegram(ctx, cfg, handler, zap.NewNop(), store)

	if !waitFor(t, 5*time.Second, func() bool { return store.current() >= 102 }) {
		t.Fatalf("offset was not persisted, got %d", store.current())
	}

	received := handler.all()
	if len(received) != 1 || received[0] != "新訊息" {
		t.Fatalf("expected only the new message to be answered, got %#v", received)
	}
	for _, text := range received {
		if text == "历史积压消息" {
			t.Fatal("backlog message was answered on startup")
		}
	}

	mu.Lock()
	defer mu.Unlock()
	sawProbe := false
	for _, q := range queries {
		if strings.Contains(q, "offset=-1") {
			sawProbe = true
			break
		}
	}
	if !sawProbe {
		t.Fatalf("expected a backlog probe with offset=-1, queries=%#v", queries)
	}
	if len(sent) != 1 {
		t.Fatalf("expected exactly one reply, got %#v", sent)
	}
}

func TestTelegramPollResumesFromPersistedOffset(t *testing.T) {
	var mu sync.Mutex
	var queries []string
	var sent []string
	srv := newFakeTelegramServer(t, &queries, &sent, &mu)

	oldBase := telegramAPIBase
	telegramAPIBase = srv.URL
	defer func() { telegramAPIBase = oldBase }()

	store := &fakeOffsetStore{offset: 500}
	handler := &fakeMessageHandler{}
	cfg := config.RobotsConfig{Telegram: config.RobotTelegramConfig{
		Enabled:     true,
		BotToken:    "TOKEN",
		BotUsername: "scanbot",
	}}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go StartTelegram(ctx, cfg, handler, zap.NewNop(), store)

	if !waitFor(t, 5*time.Second, func() bool { return store.current() >= 502 }) {
		t.Fatalf("offset was not advanced, got %d", store.current())
	}
	received := handler.all()
	if len(received) != 1 || received[0] != "重啟後新訊息" {
		t.Fatalf("expected the post-restart message to be answered, got %#v", received)
	}

	mu.Lock()
	defer mu.Unlock()
	for _, q := range queries {
		if strings.Contains(q, "offset=-1") {
			t.Fatalf("restart must not probe the backlog again, queries=%#v", queries)
		}
	}
}
