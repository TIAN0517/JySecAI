package mcp

import (
	"context"
	"errors"
	"testing"
	"time"

	"cyberstrike-ai/internal/config"

	"go.uber.org/zap"
)

// newHealthTestConfig 建立一個模式上啟用、但 command 不存在的 stdio 設定，
// 用來在受控環境下驗證「自動拉起」的完整路徑（連線必然失敗並留下 error 狀態）。
func newHealthTestConfig(name string) config.ExternalMCPServerConfig {
	return config.ExternalMCPServerConfig{
		Type:              "stdio",
		Command:           "nonexistent-jysecai-health-cmd",
		ExternalMCPEnable: true,
		Timeout:           1,
	}
}

func waitFor(t *testing.T, timeout time.Duration, what string, cond func() bool) {
	t.Helper()
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		if cond() {
			return
		}
		time.Sleep(20 * time.Millisecond)
	}
	t.Fatalf("等待超時: %s", what)
}

// 情境 A：設定已啟用但完全沒有客戶端（例如服務剛啟動），
// 監督循環應把該 server 自動拉起（建立 client 並嘗試連線）。
func TestHealthSupervisor_EnabledWithoutClient_AutoStarts(t *testing.T) {
	manager := NewExternalMCPManager(zap.NewNop())
	t.Cleanup(manager.StopAll)

	manager.AddOrUpdateConfig("alpha", newHealthTestConfig("alpha"))

	manager.runHealthCheck()

	waitFor(t, 3*time.Second, "自動拉起（建立 client 並留下錯誤狀態）", func() bool {
		manager.mu.RLock()
		client, has := manager.clients["alpha"]
		status := ""
		if has {
			status = client.GetStatus()
		}
		manager.mu.RUnlock()
		return has && (status == "error" || status == "connecting")
	})
}

// deadClient 是 IsConnected()==false 的假 client，模擬已存在的死連線。
type deadClient struct{}

func (c *deadClient) Initialize(ctx context.Context) error { return nil }
func (c *deadClient) ListTools(ctx context.Context) ([]Tool, error) { return nil, nil }
func (c *deadClient) CallTool(ctx context.Context, name string, args map[string]interface{}) (*ToolResult, error) {
	return nil, errors.New("dead")
}
func (c *deadClient) Ping(ctx context.Context) error { return errors.New("not connected") }
func (c *deadClient) Close() error                  { return nil }
func (c *deadClient) IsConnected() bool             { return false }
func (c *deadClient) GetStatus() string             { return "error" }

// 情境 B：client 存在但處於未連線狀態，監督循環應觸發重連（client 被替換重建）。
func TestHealthSupervisor_DisconnectedClient_AutoRestarts(t *testing.T) {
	manager := NewExternalMCPManager(zap.NewNop())
	t.Cleanup(manager.StopAll)

	manager.AddOrUpdateConfig("beta", newHealthTestConfig("beta"))

	injected := &deadClient{}
	manager.mu.Lock()
	manager.clients["beta"] = injected
	manager.mu.Unlock()

	manager.runHealthCheck()

	waitFor(t, 3*time.Second, "未連線 client 被替換重建", func() bool {
		manager.mu.RLock()
		current, has := manager.clients["beta"]
		manager.mu.RUnlock()
		return has && current != injected
	})
}

// faltyPingClient 是 IsConnected()==true 但 Ping 回報傳輸層斷連的假 client，
// 用來驗證「已連線但 ping 偵測到死亡」會被路由到 handleConnectionDead。
type faultyPingClient struct {
	failingExternalMCPClient
}

func (c *faultyPingClient) Ping(ctx context.Context) error {
	return errors.New("connection reset by peer")
}

// 情境 C：已連線 client 的 Ping 回傳連線級錯誤，監督循環應路由到
// handleConnectionDead（記錄「連接已斷開」並清空工具數）。
func TestHealthSupervisor_PingConnectionDead_RoutesToRecovery(t *testing.T) {
	manager := NewExternalMCPManager(zap.NewNop())
	t.Cleanup(manager.StopAll)

	manager.AddOrUpdateConfig("gamma", newHealthTestConfig("gamma"))
	manager.mu.Lock()
	manager.clients["gamma"] = &faultyPingClient{}
	manager.mu.Unlock()
	manager.toolCountsMu.Lock()
	manager.toolCounts["gamma"] = 7
	manager.toolCountsMu.Unlock()

	manager.runHealthCheck()

	waitFor(t, 2*time.Second, "記錄「連接已斷開」", func() bool {
		manager.mu.RLock()
		defer manager.mu.RUnlock()
		msg := manager.errors["gamma"]
		return containsFold(msg, "连接已断开")
	})

	// handleConnectionDead/markClientDisconnected 同步清空工具数并丢弃工具缓存，
	// 不会再被后台刷新以「新鮮緩存」名義復活。這裡同時等待斷連後的重建不致回寫非 0。
	manager.toolCountsMu.RLock()
	count := manager.toolCounts["gamma"]
	manager.toolCountsMu.RUnlock()
	if count != 0 {
		t.Fatalf("toolCounts[gamma] = %d, 期望 0（斷連後應清空）", count)
	}
}

// 情境 D：已連線且 ping 正常時，不應觸發任何重連/錯誤。
func TestHealthSupervisor_HealthyClient_NoReconnect(t *testing.T) {
	manager := NewExternalMCPManager(zap.NewNop())
	t.Cleanup(manager.StopAll)

	manager.AddOrUpdateConfig("delta", newHealthTestConfig("delta"))
	manager.mu.Lock()
	manager.clients["delta"] = newBlockingExternalMCPClient("ok")
	manager.mu.Unlock()

	manager.runHealthCheck()
	manager.runHealthCheck()

	manager.mu.RLock()
	errMsg, hasErr := manager.errors["delta"]
	_, hasClient := manager.clients["delta"]
	manager.mu.RUnlock()
	if hasErr && errMsg != "" {
		t.Fatalf("健康 server 不應有錯誤，got %q", errMsg)
	}
	if !hasClient {
		t.Fatal("健康 server 的 client 不應被移除")
	}
}

func containsFold(s, sub string) bool {
	return len(s) >= len(sub) && (func() bool {
		var i int
		for i = 0; i+len(sub) <= len(s); i++ {
			if foldEqual(s[i:i+len(sub)], sub) {
				return true
			}
		}
		return false
	})()
}

func foldEqual(a, b string) bool {
	if len(a) != len(b) {
		return false
	}
	for i := 0; i < len(a); i++ {
		ca, cb := a[i], b[i]
		if 'A' <= ca && ca <= 'Z' {
			ca += 'a' - 'A'
		}
		if 'A' <= cb && cb <= 'Z' {
			cb += 'a' - 'A'
		}
		if ca != cb {
			return false
		}
	}
	return true
}