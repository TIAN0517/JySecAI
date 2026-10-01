# POC/EXP — https://epcr.tpf.gov.tw:4004/login 存在未处理异常导致登录服务全量 500 

> 漏洞ID: `de2639e3-d55b-44a7-b5eb-ff1cf4156690`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4004/login (AuthServer login endpoint)`

**類型**: Availability / Broken Authentication (unhandled 500 on login)

## 描述

The authentication server's login endpoint (https://epcr.tpf.gov.tw:4004/login) returns an unhandled 500 Internal Server Error with body `"TypeError"` (11 bytes, content-type application/json) for essentially any POST body. Reproduced with well-formed login payloads matching the client's documented format `{"username","password","captcha","domain":"AUTH_SERVER"}` (JSON, Content-Type application/json), with and without the `connect.sid` session cookie issued by GET /captcha, and with empty/malformed payloads. The 500 also sets a fresh connect.sid cookie, confirming the request reached the Express login handler and the server threw an uncaught JavaScript TypeError rather than returning a proper validation/auth error. This is a universal server-side crash on the primary authentication entry point.

## POC / 復現步驟

```
Request:
  POST /login HTTP/1.1
  Host: epcr.tpf.gov.tw:4004
  Content-Type: application/json
  Body: {"username":"admin","password":"admin","captcha":"test","domain":"AUTH_SERVER"}

Response:
  HTTP/1.1 500 Internal Server Error
  content-type: application/json; charset=utf-8
  content-length: 11
  set-cookie: connect.sid=s%3Ayzj8KaqE8OAHaIbRQlYzvy7TcIdNzfoR...; Path=/; HttpOnly
  Body: "TypeError"

Reproduced identically with: (a) no session cookie, (b) valid connect.sid from GET /captcha, (c) empty body, (d) missing fields. All return HTTP 500 with body "TypeError". A correctly-functioning endpoint would return 401/400 (bad credentials / invalid captcha), not a 500 stack-level TypeError.
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
