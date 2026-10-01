# 4005/4007 端口 /config 端点未授权访问，泄露完整微服务配置

- ID: `f79bfb03-894e-4dbd-905f-a8c348054fcc`
- Severity: **medium**
- Status: confirmed
- Type: 信息泄露
- Target: `https://epcr.tpf.gov.tw:4005/config 和 https://epcr.tpf.gov.tw:4007/config`
- Conversation: `667feba8-aeb6-43db-baa4-1e16ab996122`
- Created: 2026-08-29 07:39:01.301257089+08:00

## Description

4005 (MonitorServer) 和 4007 (EPCRServer/StatServer) 的 /config 端点无需认证即可访问，返回完整的应用配置 JSON，泄露微服务拓扑、版本号、RTMP 直播流地址、Socket.IO 配置等敏感信息。

## Reproduction

1. 使用 curl 发送 GET 请求到 4005 端口的 /config 端点：
   ```bash
   curl -sk https://epcr.tpf.gov.tw:4005/config
   ```
2. 观察响应：返回 200 状态码，Body 为完整配置 JSON
3. 验证配置内容包含：
   - version: 1.6.26080
   - 所有微服务 URL（epcrServer, vitalSignVideoServer, 等）
   - RTMP 直播流地址（merLiveStream, merLiveStreamRtmp）
   - Socket.IO 配置（socketIo）
   - 空闲检测配置（MAX_IDLE_DURATION, NO_IDLE_DETECTION_STATES）
4. 重复测试 4007 端口：
   ```bash
   curl -sk https://epcr.tpf.gov.tw:4007/config
   ```
5. 确认返回相同内容

## Evidence

--- retest 2026-08-31 ---
2026-08-31 整理：并入 c8a878fa（4005/4007 /config）。
```bash
$ curl -sk https://epcr.tpf.gov.tw:4005/config
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

{
  "version": "1.6.26080",
  "epcrServer": "https://epcr.tpf.gov.tw:4000",
  "vitalSignVideoServer": "https://epcr.tpf.gov.tw:4001",
  "hospitalServer": "https://epcr.tpf.gov.tw:4002",
  "doctorServer": "https://epcr.tpf.gov.tw:4003",
  "authServer": "https://epcr.tpf.gov.tw:4004",
  "monitorServer": "https://epcr.tpf.gov.tw:4005",
  "merBridge": "https://epcr.tpf.gov.tw:4006",
  "statServer": "https://epcr.tpf.gov.tw:4007",
  "mciServer": "https://epcr.tpf.gov.tw:4008",
  "printServer": "http://epcr.tpf.gov.tw:9000",
  "merServer": "https://mer2.tpf.gov.tw:7000",
  "merLiveStream": "https://mer2voip.tpf.gov.tw:30080/live?app=rtmp&stream=live${dispatchRecordUuid}",
  "merLiveStreamRtmp": "rtmp://mer2voip.tpf.gov.tw/rtmp/live",
  "cloudPortal": "https://cloud2.ntpc.gov.tw",
  "socketIo": {
    "socketServerUrl": "https://epcr.tpf.gov.tw:4005",
    "socketServerPath": "socket.io",
    "reconnection": true,
    "reconnectionAttempts": 2147483647,
    "reconnectionDelay": 100,
    "reconnectionDelayMax": 5000,
    "randomizationFactor": 0.5
  },
  "MAX_IDLE_DURATION": 900000,
  "NO_IDLE_DETECTION_STATES": ["login", "caseDetailPrint"]
}

$ curl -sk https://epcr.tpf.gov.tw:4007/config
HTTP/1.1 200 OK
(相同内容)
```

## Impact

1. **信息泄露**：攻击者可以获取完整的微服务架构，了解系统各组件的功能和交互方式
2. **攻击面扩大**：泄露的 RTMP 直播流地址和 Socket.IO 配置为后续攻击提供线索
3. **版本指纹**：泄露版本号 1.6.26080，便于攻击者查找对应的已知漏洞
4. **配置细节**：泄露 Socket.IO 重连策略（reconnectionAttempts: 2147483647），可能导致连接风暴
5. **业务逻辑**：泄露空闲检测配置（MAX_IDLE_DURATION: 900000ms = 15分钟），了解用户会话管理策略

## Recommendation

1. **添加认证**：为 /config 端点添加认证机制，仅允许已认证用户访问
2. **最小化暴露**：移除或简化 /config 返回的信息，仅返回前端必需的字段
3. **环境分离**：生产环境使用精简配置，开发/测试环境使用完整配置
4. **访问控制**：限制 /config 端点的访问 IP 或添加 API 密钥
5. **版本控制**：考虑隐藏或混淆版本号，减少指纹识别
