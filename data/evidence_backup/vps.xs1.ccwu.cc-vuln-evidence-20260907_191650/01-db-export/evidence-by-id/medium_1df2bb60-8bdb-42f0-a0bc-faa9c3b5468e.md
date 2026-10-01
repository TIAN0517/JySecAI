# 4004 authServer /captcha 端点无认证暴露（登录爆破前置）

- ID: `1df2bb60-8bdb-42f0-a0bc-faa9c3b5468e`
- Severity: **medium**
- Status: open
- Type: 未授权访问 / 验证码滥用
- Target: `https://epcr.tpf.gov.tw:4004/captcha`
- Conversation: `c540ef6b-4c80-4589-8e93-ff57dd1bb32e`
- Created: 2026-08-29 20:41:12.009406907+08:00

## Description

4004 authServer GET /captcha 无需任何认证即可获取验证码图片（GIF89a 17646B），且服务端返回 set-cookie: connect.sid=s%3A...（express-session）。攻击者可无限获取验证码，配合 /login POST 端点进行登录爆破。每次获取验证码会重置 connect.sid session，使任何基于 IP 的速率限制失效。

## Preconditions

无（无需任何凭证）

## Reproduction

1. curl -k 'https://epcr.tpf.gov.tw:4004/captcha' -o /tmp/captcha.gif
2. file /tmp/captcha.gif → "GIF89a"
3. 循环 10 次请求，每次都返回 200 OK + 新 GIF + 新 connect.sid
4. 配合 /login POST 端点尝试登录爆破（需构造正确的 captcha 答案 + username + password）

## Evidence

步骤 1：curl -k 'https://epcr.tpf.gov.tw:4004/captcha' -o /tmp/captcha.gif
响应：
HTTP/1.1 200 OK
content-type: application/octet-stream
content-length: 17646
set-cookie: connect.sid=s%3A...; HttpOnly
body: GIF89a (开头标识)

文件大小 17646B 表明是真实 GIF 验证码图片（不是占位符）

步骤 2：多次连续请求 /captcha
每次都返回 200 OK + 新的 GIF + 新的 connect.sid，表明：
- 无认证要求
- 无速率限制
- 每次获取都会创建新 session

步骤 3：对比 /version 端点
GET /version 返回 401 "No authorization token was found"，说明 express-jwt 中间件存在但未覆盖 /captcha 路由

## Impact

1. 登录爆破前置：可无限获取验证码配合 /login POST 进行无限制爆破尝试
2. Session 创建滥用：每次请求创建新 session，可能导致 session 存储溢出
3. 信息泄露：GIF 验证码内容（虽然仅是随机字符）可被用于推断验证码生成算法
4. 配合 mixed pattern 漏洞：Web 鉴权严格但 /captcha 暴露，可作为攻击者探测鉴权逻辑的入口

## Recommendation

1. 对 /captcha 路由添加 express-jwt 鉴权或独立的 session 验证中间件
2. 实施基于 IP + session 的速率限制（如每分钟最多获取 5 次验证码）
3. CAPTCHA 答案必须与 session 绑定，验证后立即销毁
4. 添加 CAPTCHA 复杂度（扭曲、干扰线、动态背景）
5. 记录异常获取模式，触发风控告警
