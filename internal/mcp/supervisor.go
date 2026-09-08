package mcp

import (
	"context"
	"sort"
	"time"

	"go.uber.org/zap"
)

// externalMCPHealthCheckInterval 健康检查监督循环的周期：断连的 stdio/HTTP 子进程
// 会在该间隔内被检测并自动拉起（配合 reconnectBackoff 的退避重试）。
const externalMCPHealthCheckInterval = 15 * time.Second

// externalMCPHealthCheckTimeout 单次健康检查（Ping）的超时。
const externalMCPHealthCheckTimeout = 5 * time.Second

// startHealthSupervisor 启动周期性的主动健康检查 goroutine。
//
// 背景机制：原先只在 ListTools/CallTool 或 60 秒工具刷新时才探测断连；
// 当 stdio 子进程在空闲时退出时，可能要等很久才会被发现。本监督循环定时：
//  1. 已启用但没有客户端 -> 立即调度自动拉起；
//  2. 客户端存在但未连接 -> 标记断连并调度重连；
//  3. 客户端已连接 -> 发送 MCP ping，若返回传输层断连错误则标记并调度重连。
//
// 重连仍复用 scheduleReconnect 的退避逻辑，避免 ping 高频失败时打满资源。
func (m *ExternalMCPManager) startHealthSupervisor() {
	m.refreshWg.Add(1)
	go func() {
		defer m.refreshWg.Done()
		ticker := time.NewTicker(externalMCPHealthCheckInterval)
		defer ticker.Stop()

		// 启动后立即执行一次健康检查，尽快收敛初始状态。
		m.runHealthCheck()
		m.refreshToolCounts()

		for {
			select {
			case <-ticker.C:
				m.runHealthCheck()
			case <-m.stopRefresh:
				return
			}
		}
	}()
}

// runHealthCheck 对启用的 server 逐一执行健康检查。
func (m *ExternalMCPManager) runHealthCheck() {
	type entry struct {
		client    ExternalMCPClient
		hasClient bool
	}
	m.mu.RLock()
	checks := make(map[string]entry)
	for name, cfg := range m.configs {
		if !m.isEnabled(cfg) {
			continue
		}
		checks[name] = entry{client: m.clients[name], hasClient: m.clients[name] != nil}
	}
	m.mu.RUnlock()

	names := make([]string, 0, len(checks))
	for name := range checks {
		names = append(names, name)
	}
	sort.Strings(names)

	for _, name := range names {
		e := checks[name]
		m.checkClientHealth(name, e.client, e.hasClient)
	}
}

// checkClientHealth 对单个 server 执行健康检查并在必要时触发自动拉起。
func (m *ExternalMCPManager) checkClientHealth(name string, client ExternalMCPClient, hasClient bool) {
	if !hasClient || client == nil {
		// 已启用但没有客户端（例如进程刚启动、或之前从未拉起成功）。
		m.logger.Debug("健康检查：外部MCP已启用但无客户端，调度自动拉起",
			zap.String("name", name),
		)
		m.scheduleReconnect(name)
		return
	}

	if !client.IsConnected() {
		if client.GetStatus() == "connecting" {
			// 连接进行中，等待下次健康检查，不打断 in-flight connect。
			return
		}
		m.logger.Warn("健康检查：外部MCP客户端未连接，调度自动拉起",
			zap.String("name", name),
			zap.String("status", client.GetStatus()),
		)
		m.markClientDisconnected(name, client, nil)
		m.scheduleReconnect(name)
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), externalMCPHealthCheckTimeout)
	err := client.Ping(ctx)
	cancel()

	if err == nil {
		return
	}
	if isConnectionDeadError(err) {
		m.handleConnectionDead(name, client, err)
		return
	}
	// 非传输层断连（如偶发超时）不触发重连，避免连接抖动。
	m.logger.Debug("健康检查：外部MCP ping 非致命错误",
		zap.String("name", name),
		zap.Error(err),
	)
}