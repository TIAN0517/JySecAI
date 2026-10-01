package security

import (
	"jysecai/internal/config"
	"jysecai/internal/observability"
	"jysecai/internal/toolschema"
	"jysecai/internal/tooltarget"
)

// WireScannerRuntime builds the scanner pre-exec pipeline from the supplied
// SecurityConfig and wires it into the Executor.
//
// Behavior contract:
//
//   - If cfg.Scanner.AuthorizedTargets is empty (the default), every
//     external scanner call is rejected with TARGET_NOT_AUTHORIZED before
//     the tool process starts. There is no implicit allow-all.
//   - The policy uses exact-match only: subdomain tricks cannot bypass
//     the allowlist (see ConfigAuthorizedTargetPolicy).
//   - ExecutionMode governs the additional_args gate. The Agent path
//     must use ExecutionModeAgent; the stdio/operator path must use
//     ExecutionModeManual.
//
// Returns the metrics registry so the caller can wire it into observability
// exports (Prometheus, OTel, structured logs).
func WireScannerRuntime(exec *Executor, cfg *config.SecurityConfig, mode ExecutionMode) *observability.Registry {
	tools := toolsForWire(cfg)
	registry := toolschema.NewRegistry()
	registry.Set(toolschema.NewSnapshot(tools))
	policy := tooltarget.NewConfigAuthorizedTargetPolicy()
	policy.Replace(tooltarget.Config{Entries: tooltarget.FromConfigAuthorizedTargets(cfg.Scanner.AuthorizedTargets)})
	metrics := observability.New()
	exec.SetScannerHooks(registry, policy, metrics, mode)
	return metrics
}

// toolsForWire picks the canonical tool list for schema construction. Today
// only the inline Tools slice is supported; ToolsDir files are picked up
// later by Executor.RegisterTools via the directory loader.
func toolsForWire(cfg *config.SecurityConfig) []config.ToolConfig {
	if cfg == nil {
		return nil
	}
	return cfg.Tools
}