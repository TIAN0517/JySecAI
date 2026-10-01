# vps.xs1.ccwu.cc 漏洞證據備份

- 來源主機：`vps.xs1.ccwu.cc`（本機 CyberStrikeAI）
- 匯出時間：20260907_191650
- 資料庫：`/opt/CyberStrikeAI/data/conversations.db`
- 工作區：`/opt/CyberStrikeAI/tmp/workspace/`

## 數量

- 漏洞總數：588
- 有證據（evidence > 20 字）：124
- 優先完整匯出（有證據 / confirmed / critical / high）：147
- 已確認：34
- 嚴重 critical：24
- 高危 high：60

### 有證據漏洞依嚴重度

{
  "medium": 43,
  "high": 37,
  "low": 17,
  "critical": 24,
  "info": 3
}

### 有證據漏洞依狀態

{
  "open": 87,
  "confirmed": 34,
  "ignored": 3
}

## 目錄說明

- `01-db-export/vulnerabilities_with_evidence.json`：124 筆含證據全文
- `01-db-export/vulnerabilities_priority_full.json`：優先漏洞完整欄位
- `01-db-export/evidence-by-id/`：每筆證據獨立 Markdown
- `02-index/all_vulnerabilities_index.json`：全部漏洞索引（不含證據正文）
- `03-workspace/`：對話/專案工作區檔案（已排除 rockyou、node_modules、wordlist）
- `04-extra-evidence/`：額外證據目錄

## 已複製工作區

[
  {
    "kind": "conversation",
    "id": "0e6944a5-643d-4cd9-9a2a-7b1676a25139",
    "title": "授权目标 https://epcr.tpf.gov.tw:4000/ 第2波完整漏洞扫描，不要停。...",
    "files": 101
  },
  {
    "kind": "conversation",
    "id": "13579e17-54d6-45c5-9325-bcbbed1e1ea4",
    "title": "https://ofa377.com.tw/",
    "files": 5
  },
  {
    "kind": "conversation",
    "id": "1c8c904f-b8ea-486f-95a1-aaf59a4fa38d",
    "title": "https://epcr.tpf.gov.tw:4005/",
    "files": 7
  },
  {
    "kind": "conversation",
    "id": "532cedc0-0580-4045-a5e2-45c07c488867",
    "title": "https://epcr.tpf.gov.tw:4004/",
    "files": 101
  },
  {
    "kind": "conversation",
    "id": "60e32c09-22bf-4923-8a45-c5685b45ef65",
    "title": "https://www.smart-taoyuan.tw/",
    "files": 4
  },
  {
    "kind": "conversation",
    "id": "80d7d5eb-ea76-4288-bfcf-c45dee0eace1",
    "title": "授权目标 https://epcr.tpf.gov.tw:4000/ 第3波完整漏洞扫描，不要停。...",
    "files": 10
  },
  {
    "kind": "conversation",
    "id": "aaadea7a-5b5b-4a24-af28-d7bd09fb924d",
    "title": "http://csogmes168.com/",
    "files": 4
  },
  {
    "kind": "conversation",
    "id": "b87b7362-e146-46d2-b424-6fb799b8e23a",
    "title": "https://www.land.nat.gov.tw/",
    "files": 11
  },
  {
    "kind": "conversation",
    "id": "c471694d-29e0-4e5b-b3d6-93d775994da8",
    "title": "https://www.letsmakeaplan.org/\nhttps://www.cfp....",
    "files": 2
  },
  {
    "kind": "conversation",
    "id": "db0e169e-2aa4-4b11-9bcd-0304a08f2216",
    "title": "https://epcr.tpf.gov.tw:4006/",
    "files": 1
  },
  {
    "kind": "conversation",
    "id": "df6df6cb-6530-4598-9384-9f0e57a9ed03",
    "title": "https://smartcity.kcg.gov.tw/",
    "files": 10
  },
  {
    "kind": "project",
    "id": "b19751aa-c845-42e9-adca-e4cd170b0d5b",
    "title": "ttww",
    "files": 159
  },
  {
    "kind": "project",
    "id": "cda6ab9b-2296-4103-b1f0-10410de2eca8",
    "title": "tw",
    "files": 848
  },
  {
    "kind": "extra",
    "id": "gcp-a-jwt-evidence",
    "title": "JWT evidence",
    "files": 5
  }
]
