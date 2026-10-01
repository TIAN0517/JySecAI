package config

import "testing"

func TestRaceRegression_MCPConfigCloneNilCollections(t *testing.T) {
	copy := (ExternalMCPServerConfig{Command: "fixture"}).Clone()
	if copy.Command != "fixture" || copy.Args != nil || copy.AutoApprove != nil || copy.Env != nil || copy.Headers != nil || copy.ToolEnabled != nil {
		t.Fatal("clone changed scalar values or nil collection semantics")
	}
}
