package mcp

import (
	"sync"
	"testing"

	"go.uber.org/zap"
	"jysecai/internal/config"
)

func ownershipFixture() config.ExternalMCPServerConfig {
	return config.ExternalMCPServerConfig{
		Command: "unused-local-fixture", Args: []string{"original"},
		Env: map[string]string{"fixture": "original"}, Headers: map[string]string{"fixture": "original"},
		AutoApprove: []string{"original"}, ToolEnabled: map[string]bool{"fixture": true},
	}
}

func assertOwnedConfig(t *testing.T, c config.ExternalMCPServerConfig) {
	t.Helper()
	if c.Args[0] != "original" || c.Env["fixture"] != "original" || c.Headers["fixture"] != "original" ||
		c.AutoApprove[0] != "original" || !c.ToolEnabled["fixture"] {
		t.Fatal("configuration snapshot aliases caller-owned mutable storage")
	}
}

func TestRaceRegression_ExternalMCPConfigOwnership(t *testing.T) {
	for _, operation := range []string{"load", "add"} {
		t.Run(operation, func(t *testing.T) {
			manager := NewExternalMCPManager(zap.NewNop())
			t.Cleanup(manager.StopAll)
			input := ownershipFixture() // Disabled: no process or network transport is started.
			if operation == "load" {
				manager.LoadConfigs(&config.ExternalMCPConfig{Servers: map[string]config.ExternalMCPServerConfig{"fixture": input}})
			} else if err := manager.AddOrUpdateConfig("fixture", input); err != nil {
				t.Fatal(err)
			}
			published := manager.GetConfigs()["fixture"]
			start := make(chan struct{})
			var wg sync.WaitGroup
			wg.Add(2)
			go func() {
				defer wg.Done()
				<-start
				for i := 0; i < 1000; i++ {
					input.Args[0] = "caller-mutated"
				}
			}()
			go func() {
				defer wg.Done()
				<-start
				for i := 0; i < 1000; i++ {
					if published.Args[0] != "original" {
						t.Error("async reader observed caller mutation")
						return
					}
				}
			}()
			close(start)
			wg.Wait()
			input.Env["fixture"] = "caller-mutated"
			input.Headers["fixture"] = "caller-mutated"
			input.AutoApprove[0] = "caller-mutated"
			input.ToolEnabled["fixture"] = false
			assertOwnedConfig(t, manager.GetConfigs()["fixture"])
			// Snapshot consumers must not mutate the manager or another reader.
			returned := manager.GetConfigs()["fixture"]
			returned.Args[0] = "consumer-mutated"
			returned.Env["fixture"] = "consumer-mutated"
			returned.Headers["fixture"] = "consumer-mutated"
			returned.AutoApprove[0] = "consumer-mutated"
			returned.ToolEnabled["fixture"] = false
			assertOwnedConfig(t, manager.GetConfigs()["fixture"])
		})
	}
}

func TestRaceRegression_LazyClientConfigOwnership(t *testing.T) {
	input := ownershipFixture()
	client := newLazySDKClient(input, zap.NewNop())
	input.Args[0] = "caller-mutated"
	input.Env["fixture"] = "caller-mutated"
	input.Headers["fixture"] = "caller-mutated"
	input.AutoApprove[0] = "caller-mutated"
	input.ToolEnabled["fixture"] = false
	assertOwnedConfig(t, client.serverCfg)
}
