# JySecAI Engine Adapter Contract v1

除了 Strix CLI Driver 與 Jy Workflow HTTP Driver 外，其他引擎預定透過相同 HTTP Adapter contract 接入。這讓工具維持獨立 runtime，同時把結果轉換成一致的 Run、Finding 與 Artifact metadata。

Reference Compose 的 `/governance/` 是使用者介面，公開 `/v1/*` 是 JySecAI control-plane API。下述 `POST /v1/jobs/execute` 則是 Worker 對各 Adapter base URL 發出的請求；它不由 JySecAI Gateway 代替 Adapter 實作。

## 目前實作狀態

本倉庫已實作 `UniformHttpDriver` client、response schema 驗證與控制面的 Finding／Artifact metadata 寫入，但**沒有提供下列引擎的 Adapter server 或容器映像**：

| 引擎 | 本倉庫目前提供 | 部署者仍須提供 |
|---|---|---|
| Promptfoo | HTTP client、catalog metadata | Promptfoo runtime 與相容 Adapter service |
| PyRIT | HTTP client、catalog metadata | PyRIT runtime 與相容 Adapter service |
| Giskard | HTTP client、catalog metadata | Giskard runtime 與相容 Adapter service |
| ART | HTTP client、catalog metadata | ART／GPU runtime 與相容 Adapter service |
| Humanbound | HTTP client、選配 catalog metadata | 合法可用的 runtime 與相容 Adapter service |
| AD Risk Audit | HTTP client、唯讀 profile 定義 | 分離的 Windows／AD audit service 與相容 Adapter |

只有在對應 `JYSEC_ENGINE_<ENGINE>_URL` 已設定時，控制面才會把這些引擎視為已配置。現階段這只驗證設定存在，不會證明服務在線、版本相容、尚有 capacity 或已完成合法 target E2E。

## Endpoint

`POST /v1/jobs/execute`

Headers：

- `Content-Type: application/json`
- `Authorization: Bearer <JYSEC_ENGINE_ADAPTER_TOKEN>`（若有配置）

Request：

```json
{
  "schemaVersion": 1,
  "run": {
    "id": "run_...",
    "tenantId": "tenant-1",
    "projectId": "project-1",
    "engine": "promptfoo",
    "profile": "standard",
    "targets": ["https://staging.example.com"],
    "objective": "Authorized validation objective",
    "authorization": {
      "id": "AUTH-2026-001",
      "targetPatterns": ["*.example.com"],
      "operations": ["ai_red_team"],
      "validFrom": "2026-09-02T00:00:00.000Z",
      "validUntil": "2026-09-09T00:00:00.000Z",
      "attested": true
    }
  }
}
```

實際 Request 會包含完整 `SecurityRun` 欄位。Adapter 必須把 authorization 視為不可變邊界；若引擎無法遵守，應失敗而不是擴大目標。

Response：

```json
{
  "externalRunId": "engine-job-123",
  "summary": {
    "tests": 84,
    "passed": 80,
    "failed": 4
  },
  "findings": [
    {
      "engineVersion": "1.2.3",
      "testCaseId": "LLM-PI-004",
      "category": "prompt-injection",
      "title": "Indirect instruction changed tool behavior",
      "severity": "high",
      "confidence": 0.96,
      "status": "confirmed",
      "evidenceRefs": ["evidence/LLM-PI-004.json"],
      "reproductionSummary": "Reproduced twice within the approved test harness.",
      "counterevidence": "Control prompt remained blocked.",
      "remediation": "Treat retrieved text as untrusted data and gate tool calls.",
      "fingerprint": "llm-pi-004-v1"
    }
  ],
  "artifacts": [
    {
      "kind": "test-transcript",
      "objectKey": "evidence/LLM-PI-004.json",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "mediaType": "application/json",
      "sizeBytes": 2048,
      "encrypted": true
    }
  ]
}
```

## 驗證規則

- Response 不接受未聲明欄位。
- 每次最多 500 findings 與 500 artifacts；大量輸出應切分或上傳至物件儲存。
- Finding confidence 為 `0..1`，status 為 `suspected|confirmed|inconclusive|resolved`。
- Artifact key 必須是安全相對路徑，不得包含 `.`、`..`、反斜線或前導 `/`。
- Artifact 必須由 Adapter 宣告為已加密，並帶 64 位小寫 SHA-256；控制面目前只驗證 metadata 格式，不會讀取本體以驗證加密或 checksum。
- 控制面會自行加入 tenant／project／run namespace，並重新產生全域 finding fingerprint。
- 不符合契約的 Adapter response 會使 Run 轉為 `failed`。目前這類 Driver 錯誤通常會被正常 ACK，不保證同時寫入 Redis dead-letter stream；DLQ 主要接收 Worker 外層未處理失敗。

## v1 契約限制

- `POST /v1/jobs/execute` 是同步呼叫；尚未定義非同步 job handle、callback、polling 或 checkpoint。
- 尚未定義標準 `health`／`capabilities`／`version`／`capacity` endpoint。這些屬於下一版 Adapter discovery Roadmap。
- Redis cancel 訊息目前只能直接終止 Worker 管理的本機 child process；通用 HTTP Adapter 沒有標準遠端 cancel endpoint。
- Findings 與 Artifacts 每次 response 最多各 500 筆；大量結果必須由 Adapter 自行切分，或先存入部署者提供的物件儲存。
- Artifact 本體不經此 API，且 JySecAI 尚未內建 S3／MinIO upload/download 流程。
- 共用 `JYSEC_ENGINE_ADAPTER_TOKEN` 是 reference 設定；正式多租戶部署應改用每 Adapter 服務身份、短效憑證或 mTLS。

## 建議部署

每一種引擎應使用獨立服務帳號、網路政策、CPU／GPU 配額與 image digest。不要讓 Promptfoo、PyRIT、ART 或 AD Worker 共用 Strix 的 Docker socket 權限。

在把 Adapter URL 設為 production 可用前，至少完成：

1. 固定引擎與 Adapter 版本，產生 SBOM 並簽署映像。
2. 驗證 Bearer token／mTLS、出站 allowlist、資源限制與 timeout。
3. 以專用且已書面授權的 staging target 跑完整 E2E。
4. 驗證格式錯誤、timeout、取消、重送與控制面 callback 失敗的行為。
5. 驗證 Artifact 本體已實際加密、SHA-256 正確且只有授權 tenant 可以下載。
