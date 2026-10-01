# 4001 VitalSignVideoServer socket.io 匿名握手（无认证）且 CORS:*

- ID: `f43b3819-ffec-4668-9eb8-9b81deed77aa`
- Severity: **medium**
- Status: open
- Type: 未授权访问/实时数据旁路
- Target: `https://epcr.tpf.gov.tw:4001/socket.io`
- Conversation: `0e6944a5-643d-4cd9-9a2a-7b1676a25139`
- Created: 2026-09-06 15:18:06.483889134+08:00

## Description

4001 VitalSignVideoServer 的 socket.io 实时通道（/socket.io/）无需任何认证即可完成握手：GET /socket.io/?EIO=3&transport=polling 返回 HTTP 200 并下发会话 sid（如 {"sid":"xfyCYQrIq8_Ys3lSA6yK","upgrades":["websocket"],"pingInterval":25000,"pingTimeout":60000}）。该服务承载急救（EMS）实时影音/生命体征推送，socket.io 握手未校验 Authorization 头，且响应带 Access-Control-Allow-Origin: *，意味着任意第三方站点可通过浏览器 JS 匿名连接该 socket 并订阅实时事件流。

## Reproduction

1. curl -sS -k "https://epcr.tpf.gov.tw:4001/socket.io/?EIO=3&transport=polling"
2. 观察：HTTP 200，返回 97:0{"sid":"..."}（匿名握手成功，无需 token）。
3. curl -sS -k -I "https://epcr.tpf.gov.tw:4001/socket.io/?EIO=3&transport=polling" | grep -i access-control-allow-origin → Access-Control-Allow-Origin: *

## Evidence

curl -sS -k "https://epcr.tpf.gov.tw:4001/socket.io/?EIO=3&transport=polling"
# → HTTP 200, body: 97:0{"sid":"xfyCYQrIq8_Ys3lSA6yK","upgrades":["websocket"],"pingInterval":25000,"pingTimeout":60000}
# 无需 Authorization 头。
# CORS:
curl -sS -k -I "https://epcr.tpf.gov.tw:4001/socket.io/?EIO=3&transport=polling" | grep -i access-control-allow-origin
# → Access-Control-Allow-Origin: *

## Impact

未认证的浏览器端 socket 客户端（含第三方页面借助 CORS:*）可连接到 4001 实时通道并取得 sid，进而订阅/监听急救实时事件（如新派遣、实时影音推送、生命体征更新），存在实时敏感数据旁路读取风险，且可被用于 DoS（大量匿名 socket 占用连接）。

## Recommendation

1) 在 4001 socket.io 服务端中间件校验 JWT（与 REST 一致），拒绝匿名握手；2) 将 socket.io 的 Access-Control-Allow-Origin 收紧为白名单域；3) 增加连接数/速率限制防止匿名连接耗尽。
