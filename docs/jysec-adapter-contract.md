# JySecAI Engine Adapter Contract v1

除了 Strix 與既有工作流核心外，其他引擎透過相同 HTTP adapter contract 接入。這讓各工具維持獨立 runtime，同時把結果沉澱成一致的商用資料模型。

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
- Artifact 必須已加密且帶 64 位小寫 SHA-256；資料本體不經此 API 傳輸。
- 控制面會自行加入 tenant／project／run namespace，並重新產生全域 finding fingerprint。
- 不符合契約的 adapter response 會使 Run 失敗並留下死信記錄。

## 建議部署

每一種引擎使用獨立服務帳號、網路政策、CPU／GPU 配額與 image digest。不要讓 Promptfoo、PyRIT、ART 或 AD Worker 共用 Strix 的 Docker socket 權限。
