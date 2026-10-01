# epcr.tpf.gov.tw:4000 前端暴露的 Google Maps API Key 无 Referrer/IP 限制可被第三方滥用

- ID: `4b464835-d2de-49e4-81c5-0f9bbca2fe6c`
- Severity: **medium**
- Status: open
- Type: 敏感信息暴露（API Key 无来源限制）
- Target: `https://epcr.tpf.gov.tw:4000/ 前端暴露的 Google Maps API Key AIzaSyB-ZbIMj6Now6cnwor9QRwjx6zEnzdYvU4`
- Conversation: `0e6944a5-643d-4cd9-9a2a-7b1676a25139`
- Created: 2026-09-06 18:59:33.746724723+08:00

## Description

EPCR 主系统前端（:4000）AngularJS SPA 在客户端配置中硬编码暴露 Google Maps API Key（AIzaSyB-ZbIMj6Now6cnwor9QRwjx6zEnzdYvU4），且该 key 未设置 HTTP Referrer / IP 限制，可被任意第三方来源跨域调用。验证：从非 epcr.tpf.gov.tw 的源 IP 直接调用 Google Maps API（geocode、distancematrix），均返回 status=OK 并成功获取地理数据（台北 lat 25.0421, lng 121.5199），证明 key 有效且无来源限制。攻击者可利用该 key 消耗配额、读取地理 API 数据、将 API 调用计费转嫁至该组织。

## Reproduction

1. 打开 https://epcr.tpf.gov.tw:4000/ ，查看前端配置或 main bundle 中的 Google Maps key（AIzaSyB-ZbIMj6Now6cnwor9QRwjx6zEnzdYvU4）。
2. 从任意非 epcr 域的 IP 执行：curl -sSk "https://maps.googleapis.com/maps/api/geocode/json?address=100%20Taipei%20Taiwan&key=AIzaSyB-ZbIMj6Now6cnwor9QRwjx6zEnzdYvU4"
3. 观察返回 status:OK 且含地理坐标（非 REQUEST_DENIED），证明 key 无 referrer/IP 限制可被任意来源调用。

## Evidence

Key 来源：4000 前端配置（/config 或 main bundle 中 Google Maps 相关配置）。验证命令：
curl -sSk "https://maps.googleapis.com/maps/api/geocode/json?address=100%20Taipei%20Taiwan&key=AIzaSyB-ZbIMj6Now6cnwor9QRwjx6zEnzdYvU4"
→ status: OK, results: 1, location: {lat: 25.0421407, lng: 121.5198716}
curl -sSk "https://maps.googleapis.com/maps/api/distancematrix/json?origins=Taipei&destinations=Kaohsiung&key=AIzaSyB-ZbIMj6Now6cnwor9QRwjx6zEnzdYvU4"
→ status: OK, rows: 1
两次调用均来自非 epcr 域的测试源 IP，返回 OK（非 REQUEST_DENIED/REFERRER_NOT_ALLOWED），证明 key 无 referrer/IP 白名单限制。

## Impact

1) 配额消耗：攻击者可用该 key 大量调用 Google Maps API，耗尽组织配额导致 EPCR 地图功能不可用（DoS）。
2) 成本转嫁：Google Maps API 超出免费配额后按量计费，攻击者产生的调用费用将计入该组织账单。
3) 地理数据读取：可读取 geocode/distance/places 等 API 返回的地理数据。
4) key 暴露于客户端 JS，任何访问前端者均可提取。

## Recommendation

1) 为该 Google Maps key 设置 HTTP Referrer 限制（仅允许 epcr.tpf.gov.tw、118.163.107.93、35.234.50.28 等白名单来源）。
2) 设置 IP 限制（仅允许可信来源 IP）。
3) 设置配额上限防止滥用。
4) 长期可考虑通过后端代理调用 Google Maps API（key 不暴露于前端）。
