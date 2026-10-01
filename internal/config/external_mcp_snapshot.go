package config

import (
	"maps"
	"slices"
)

// Clone returns an independently owned snapshot, including all mutable fields.
// The caller must keep c stable during this call. After it returns, the caller
// may reuse its slices/maps without changing the receiver's configuration.
func (c ExternalMCPServerConfig) Clone() ExternalMCPServerConfig {
	c.Args = slices.Clone(c.Args)
	c.AutoApprove = slices.Clone(c.AutoApprove)
	c.Env = maps.Clone(c.Env)
	c.Headers = maps.Clone(c.Headers)
	c.ToolEnabled = maps.Clone(c.ToolEnabled)
	return c
}
