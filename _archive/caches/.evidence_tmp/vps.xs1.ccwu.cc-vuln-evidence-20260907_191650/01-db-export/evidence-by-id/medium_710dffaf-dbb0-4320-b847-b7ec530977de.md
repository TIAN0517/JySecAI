# 4004 AuthServer /ssoLogin 与 /refreshToken 未鉴权可达并泄露差异化错误（会话枚举）

- ID: `710dffaf-dbb0-4320-b847-b7ec530977de`
- Severity: **medium**
- Status: open
- Type: 未授权访问/信息泄露
- Target: `https://epcr.tpf.gov.tw:4004/ssoLogin, https://epcr.tpf.gov.tw:4004/refreshToken`
- Conversation: `0e6944a5-643d-4cd9-9a2a-7b1676a25139`
- Created: 2026-09-06 14:49:17.315767468+08:00

## Description

4004 AuthServer 的 /ssoLogin 与 /refreshToken 端点在未认证状态下即可访问，且会根据输入返回不同的业务错误，可用于枚举/探测会话状态：/ssoLogin 空 sessionId 返回 400 "invalid sessionId"，非空未知 sessionId 返回 403 "無法辨識使用者"（说明服务端会拿 sessionId 去查用户表/会话存储）；/refreshToken 空值返回 400 "refreshToken not found"，无效值返回 400 "Invalid refresh token"。这些端点不要求任何认证即可触发后端查询逻辑并回传差异化错误，存在会话枚举与后端逻辑探测面，且为伪造/劫持 token 提供了攻击入口（若 sessionId/refreshToken 可被预测或截获）。

## Reproduction

1. curl -sS -k -X POST "https://epcr.tpf.gov.tw:4004/ssoLogin" -H "Content-Type: application/json" -d '{"sessionId":"test123"}'
2. 观察：HTTP 403 "無法辨識使用者"（无需认证即返回业务级错误）。
3. curl -sS -k -X POST "https://epcr.tpf.gov.tw:4004/refreshToken" -H "Content-Type: application/json" -d '{"refreshToken":"bad"}'
4. 观察：HTTP 400 "Invalid refresh token"。

## Evidence

# /ssoLogin 行为
curl -sS -k -X POST "https://epcr.tpf.gov.tw:4004/ssoLogin" -H "Content-Type: application/json" -d '{"sessionId":""}'
# → HTTP 400 {"message":"invalid sessionId"}
curl -sS -k -X POST "https://epcr.tpf.gov.tw:4004/ssoLogin" -H "Content-Type: application/json" -d '{"sessionId":"test123"}'
# → HTTP 403 "無法辨識使用者"  (unknown session → 查无此人)
# /refreshToken 行为
curl -sS -k -X POST "https://epcr.tpf.gov.tw:4004/refreshToken" -H "Content-Type: application/json" -d '{}'
# → HTTP 400 "refreshToken not found"
curl -sS -k -X POST "https://epcr.tpf.gov.tw:4004/refreshToken" -H "Content-Type: application/json" -d '{"refreshToken":"bad"}'
# → HTTP 400 "Invalid refresh token"
# 以上均无需 Authorization 头即可触发。

## Impact

未认证攻击者可探测 SSO/refresh 会话的存在性与有效性（差异化错误），辅助枚举有效 sessionId/refreshToken；若 SSO 的 sessionId 由外部系统（如 ntpcCloud）签发且可截获/预测，则可借此换取应用 JWT token 实现会话劫持/认证绕过。差异化错误亦辅助后端逻辑指纹识别。

## Recommendation

1) 对 /ssoLogin、/refreshToken 统一返回通用错误（避免区分"不存在"与"无效"）；2) 校验 SSO sessionId 来源（绑定签名/HMAC 或来源 IP/Referer 白名单），防止重放与枚举；3) refreshToken 使用不可预测的高熵值并限制重放窗口。
