# JySecAI 統一部署方式與生產缺口

## 先確認部署範圍

本倉庫有兩個後端應用，reference Compose 透過 Gateway 提供統一產品入口：

| 應用 | Compose 服務 | 對外入口 | 是否包含於 `compose.jysec.yml` |
|---|---|---|---|
| Go 完整主控台 | `core:8080` | `http://127.0.0.1:8787/` | 是 |
| TypeScript 治理控制面 | `control-plane:8787` | `http://127.0.0.1:8787/governance/` | 是 |

Compose 包含 PostgreSQL、Redis、Go core、治理控制面、Nginx Gateway 及選配 Worker。Gateway 預設只在 loopback 提供 HTTP；它不是公開 TLS 終結器，也不包含外部 Adapter、S3／MinIO、IdP 或 HA 元件。

Go core 由 `Dockerfile.core` 建置，公開路由由 `deploy/nginx.conf` 定義：

| Gateway 路徑 | 上游 | 說明 |
|---|---|---|
| `/` 及 Go 既有路徑 | `core:8080` | 完整主控台，包含既有 API、WebSocket 與 SSE |
| `/governance/` | `control-plane:8787` | 治理與計費頁 |
| `/assets/*`、`/v1/*`、`/metrics` | `control-plane:8787` | 治理靜態資產、API 與受 Bearer token 保護的 metrics |
| `/internal/*` | 不公開 | Gateway 回傳 `404`；Worker 直接使用 Compose 私有位址 |

## 統一 Compose 啟動

先建立不會提交至 Git 的生產環境檔：

```bash
cp platform/production.env.example platform/.env.production
chmod 600 platform/.env.production
```

至少生成 Worker、Metrics 與（若不用 JWKS）JWT 三組互不相同的 32-byte 以上秘密：

```bash
openssl rand -base64 48
openssl rand -base64 48
openssl rand -base64 48
```

分別設定 `JYSEC_JWT_SECRET`、`JYSEC_JOB_SIGNING_SECRET` 與 `JYSEC_METRICS_TOKEN`。PostgreSQL 與 Redis 必須使用不同密碼；URL 中的特殊字元要正確編碼。

```bash
docker compose -f compose.jysec.yml config
docker compose -f compose.jysec.yml up -d --build
curl -fsS http://127.0.0.1:8787/healthz
```

此命令會啟動完整主控台、治理控制面與 Gateway，但不會啟動選配 Worker。第一次啟動時，Go core 會在專用 config volume 由範例配置建立 `config.yaml`；仍需在主控台設定實際 AI channel、工具與安全邊界。治理控制面啟動時會執行 idempotent schema migration。

首次啟動會只在 core 日誌輸出一次隨機管理員密碼。立即讀取、保存於密碼管理器並登入後更換：

```bash
docker compose -f compose.jysec.yml logs core
```

Core 的 SQLite、設定、工作區、附件、Tools、Agents、Roles、Skills 與知識庫均使用個別 named volume；更新映像時會保留，但仍需建立一致性備份。Go core 目前只能維持單一 replica，請勿讓多個 core 共掛同一個 SQLite volume。

## 單獨啟動 Go 主控台（開發）

既有平台的詳細需求與配置請參考 [中文部署指南](zh-CN/deployment.md)。最短路徑為：

```bash
cp config.example.yaml config.yaml
# 設定 AI channel、工具與其他必要參數
./run.sh
```

預設配置使用自簽 HTTPS。若只在受控反向代理後使用明文內網連線，可依既有指南使用 `--http`。Go 核心目前使用 SQLite 與程序內 session；未完成 session 外部化與資料庫重構前，不應宣稱可直接水平擴展多個 replica。這個單獨啟動方式不包含 `/governance/`；若只需治理前端／API 開發，可依 README 使用 Node.js 單獨啟動。

## Worker 與引擎

Strix／Adapter Worker 是選配 profile：

```bash
docker compose -f compose.jysec.yml --profile worker up -d --build worker
```

### 實際可用性

- Strix：Worker image 已安裝 CLI，但 production 必須明確啟用，並提供 LLM 設定、Docker sandbox 與可寫 runs volume。
- Jy Workflow：Compose 已將 `JYSECAI_BASE_URL` 指向私有 `core:8080`；仍須設定有效的 `JYSECAI_SERVICE_TOKEN`，並驗證它可被 Go 核心接受。
- Promptfoo、PyRIT、Giskard、ART、Humanbound、AD Audit：必須自行部署符合 [Adapter 契約](jysec-adapter-contract.md) 的服務，再設定相應 `JYSEC_ENGINE_<ENGINE>_URL`。

配置 URL 只代表引擎可以被排入佇列，不是健康或 E2E 證明。部署者仍應主動驗證版本、認證、網路、sandbox 與合法 staging target。

### Docker socket 邊界

範例 Worker 為了讓 Strix 建立 sandbox 而掛載 Docker socket。Docker socket 等同高權限控制面，因此：

1. 僅在沒有其他商業負載的專用 VM 使用。
2. 設定正確 `DOCKER_GID`，保持容器內非 root user。
3. 以防火牆限制 Worker 只可連 Redis、control-plane、LLM provider 與已授權目標。
4. 正式環境應改用 rootless Docker、Kubernetes sandbox 或 microVM Worker。
5. AI／ML／AD Adapter 應使用不同節點及服務身份，不得共用 Strix 的 Docker socket。

## 身分與 TLS

- `JYSEC_PUBLIC_BASE_URL` 在 production 必須使用 HTTPS。
- Reference Gateway 僅綁定 `127.0.0.1:8787` 並提供 HTTP；公開部署必須把它放在 TLS／Zero Trust 反向代理或負載平衡器後方。
- 建議設定 `JYSEC_JWKS_URL`，以 IdP 的 JWKS 驗證 RS256、PS256、ES256 或 EdDSA JWT。
- 以 `JYSEC_JWT_ISSUER` 與 `JYSEC_JWT_AUDIENCE` 鎖定 token；未設定 JWKS 時才使用 HS256 secret。
- JWT 至少包含 `sub`、`tenant_id` 與 `roles`；email 可選。
- 控制面目前不提供 OIDC login redirect、SAML 或 SCIM；它只驗證上游已簽發的 token。
- Go 主控台目前使用自己的 session。統一 Gateway 不會自動讓兩套 token 相容，仍需共同 IdP 或 token exchange。
- 不得在 production 開啟 `JYSEC_DEV_AUTH`。
- `/metrics` 必須使用 `Authorization: Bearer <JYSEC_METRICS_TOKEN>`。

## Stripe

Stripe 是選配能力。若要啟用，先建立 Professional 與 Business recurring Price，填入：

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_PROFESSIONAL`
- `STRIPE_PRICE_BUSINESS`

Webhook URL 為 `https://<domain>/v1/billing/webhooks/stripe`；治理頁位於 `/governance/`。

目前已實作 Checkout、Portal 與 subscription create/update/delete Webhook。尚未實作 Stripe event-id ledger、事件順序防護、用量結算、稅務、發票流程或 Enterprise license API；正式收費前必須補齊相關營運與法律流程。

## Artifact 與資料保存

控制面目前只保存 Artifact metadata，不會傳輸或儲存檔案本體。Production 必須另外規劃物件儲存；S3／MinIO client、KMS、presigned URL 與 retention scheduler 都尚未完成。

方案中的 `auditRetentionDays` 現階段是 entitlement metadata，尚無控制面清理／封存排程，不應用它作為已落實的資料保存保證。

## 尚未完成的生產強化

- 在 reference Gateway 前部署 TLS／Zero Trust edge，並加入速率限制、WAF 與可信 proxy 設定。
- 完成 session 外部化後的 Go core HA，以及至少兩個 control-plane replica。
- PostgreSQL HA／PITR、Redis ACL／TLS／HA 與備份還原演練。
- 專用 Strix Worker，以及分離的 AI／ML／AD Adapter Worker。
- S3／MinIO evidence bucket、KMS、不可變 retention 與下載授權。
- Worker heartbeat、capacity、pending-job reclaim、retry/backoff 與 checkpoint。

## 發布前檢查

```bash
npm --prefix platform ci
npm --prefix platform run check
npm --prefix platform audit --audit-level=high
npm --prefix platform run build
node --test web/static/js/*.test.cjs
go test ./...
```

以上測試不等於外部引擎 E2E。正式發布前還應：

- 對每一個已啟用引擎使用專用、已授權 staging target 跑完整 Run。
- 驗證授權過期、越界 target、idempotency conflict 與未授權角色均被拒絕。
- 驗證 Worker crash、取消、Redis pending 工作與外部 Adapter timeout 的恢復行為。
- 驗證 Stripe Webhook 重送與亂序不會錯誤升級方案。
- 還原 PostgreSQL／SQLite／物件儲存備份並重新驗證 evidence SHA-256。
- 產生 SBOM、掃描及簽署映像，並以 digest 部署。
