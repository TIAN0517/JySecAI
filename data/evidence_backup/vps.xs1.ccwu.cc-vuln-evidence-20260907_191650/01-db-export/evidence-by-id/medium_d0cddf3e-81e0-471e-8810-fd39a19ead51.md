# 4000 端口 /config 端点未授权访问 - 泄露完整内部服务拓扑

- ID: `d0cddf3e-81e0-471e-8810-fd39a19ead51`
- Severity: **medium**
- Status: open
- Type: Information Disclosure
- Target: `https://epcr.tpf.gov.tw:4000/config`
- Conversation: `667feba8-aeb6-43db-baa4-1e16ab996122`
- Created: 2026-08-29 04:53:54.114057153+08:00

## Description

GET /config 端点无需任何认证即可访问，返回完整的系统配置 JSON，包含所有后端服务 URL、RTMP 直播地址、打印服务器、MER 服务器、云门户等内部拓扑信息。

## Reproduction

1. 发送 GET 请求：`curl -sk "https://epcr.tpf.gov.tw:4000/config"`
2. 观察响应：HTTP 200 OK
3. 检查 body：JSON 格式，包含所有后端服务 URL
4. 解析 JSON：获取 RTMP、MER、print、monitor 等服务地址

## Evidence

```
$ curl -sk "https://epcr.tpf.gov.tw:4000/config"
HTTP/1.1 200 OK
content-type: application/json; charset=utf-8
content-encoding: gzip

{"port":"4000","hostname":"https://epcr.tpf.gov.tw","vitalSignVideoServer":"https://epcr.tpf.gov.tw:4001","historyVideoPath":"/videoData/getFile/","imagePath":"/imageData/getFile/","HospitalServer":"https://epcr.tpf.gov.tw:4002","VideoPath":"rtmp://mer2voip.tpf.gov.tw/rtmp/live","authServer":"https://epcr.tpf.gov.tw:4004","doctorServer":"https://epcr.tpf.gov.tw:4003","historyVoicePath":"/voiceData/getFile/","merBridge":"https://epcr.tpf.gov.tw:4006","merServer":"https://mer2.tpf.gov.tw:7000","printServer":"http://epcr.tpf.gov.tw:9000","statUrl":"https://epcr.tpf.gov.tw:4007/statIndex.html#/","mciServer":"http://epcr.tpf.gov.tw:4008/client/","monitorServer":"http://epcr.tpf.gov.tw:4005","epcrServer":"http://epcr.tpf.gov.tw:4000","ntpcCloud":"https://cloud2.ntpc.gov.tw/home","captcha":{"enable":true,"captchaImg":"/captcha"},"MAX_IDLE_DURATION":900000,"NO_IDLE_DETECTION_STATES":["login","caseDetailPrint"],"RealTimeVideoPath":[{"path":"https://mer2voip.tpf.gov.tw:30080/live?app=rtmp&stream=live${dispatchRecordUuid}","type":"mse","isLive":true}]}
```

泄露的关键信息：
1. **所有后端服务 URL**：4001-4008, 9000
2. **RTMP 直播地址**：`rtmp://mer2voip.tpf.gov.tw/rtmp/live`
3. **实时视频流**：`https://mer2voip.tpf.gov.tw:30080/live?app=rtmp&stream=live${dispatchRecordUuid}`
4. **MER 服务器**：`https://mer2.tpf.gov.tw:7000`
5. **打印服务器**：`http://epcr.tpf.gov.tw:9000`（HTTP 而非 HTTPS）
6. **监控服务器**：`http://epcr.tpf.gov.tw:4005`（HTTP 而非 HTTPS）
7. **云门户**：`https://cloud2.ntpc.gov.tw/home`
8. **Captcha 配置**：`{"enable":true,"captchaImg":"/captcha"}`
9. **空闲超时**：900000ms（15 分钟）

## Impact

**中等-高** - 泄露完整内部服务拓扑，攻击者可：
1. **枚举所有服务**：知道所有后端微服务地址
2. **针对性攻击**：针对特定服务（如 RTMP、打印服务器）
3. **发现 HTTP 服务**：4005、9000 使用 HTTP 而非 HTTPS
4. **获取直播流**：通过 RTMP 地址观看实时视频
5. **发现云门户**：知道内部云门户地址
6. **了解业务逻辑**：知道系统有哪些功能模块

结合已发现的未授权访问漏洞（/events、/version），/config 泄露可帮助攻击者构建完整的攻击图。

## Recommendation

1. **添加认证**：要求 JWT Bearer Token
2. **过滤敏感字段**：仅返回前端必需的字段
3. **使用 HTTPS**：所有服务 URL 使用 HTTPS
4. **添加缓存**：减少频繁访问
5. **添加速率限制**：防止遍历
