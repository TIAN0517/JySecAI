# JySecAI 生產部署與強化

## 最小拓撲

- TLS／Zero Trust reverse proxy
- JySecAI control-plane（至少 2 replicas）
- PostgreSQL 17（HA／PITR）
- Redis 8（ACL、AOF、TLS 或私有網路）
- 專用 Strix Worker 節點
- 分離的 AI／ML／AD adapter Worker
- S3／MinIO 加密 evidence bucket（正式 Artifact 本體）

## 首次部署

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

將結果分別設為 `JYSEC_JWT_SECRET`、`JYSEC_JOB_SIGNING_SECRET` 與 `JYSEC_METRICS_TOKEN`。PostgreSQL 與 Redis 另外使用不同密碼；若密碼含 URL 特殊字元，`DATABASE_URL`／`REDIS_URL` 必須 URL encode。

```bash
docker compose -f compose.jysec.yml config
docker compose -f compose.jysec.yml up -d --build
curl -fsS http://127.0.0.1:8787/healthz
```

控制面啟動時自動執行 idempotent schema migration。

## 身分與 TLS

- `JYSEC_PUBLIC_BASE_URL` 在 production 必須為 HTTPS。
- 企業部署建議設定 `JYSEC_JWKS_URL`，以 IdP 的非對稱 JWKS 驗證 RS256、PS256、ES256 或 EdDSA 短效 JWT；控制面會快取金鑰並處理輪替。
- 以 `JYSEC_JWT_ISSUER`、`JYSEC_JWT_AUDIENCE` 嚴格鎖定 issuer 與 audience；未設定 JWKS 時才使用 `JYSEC_JWT_SECRET` 的 HS256 模式。
- JWT 至少包含 `sub`、`tenant_id`、`roles`；email 可選。
- 不得在 production 開啟 `JYSEC_DEV_AUTH`。
- `/metrics` 必須使用 `Authorization: Bearer <JYSEC_METRICS_TOKEN>`。

## Worker

```bash
docker compose -f compose.jysec.yml --profile worker up -d --build worker
```

範例 Worker 為了讓 Strix 建立 sandbox 而掛載 Docker socket。Docker socket 等同高權限控制面，因此：

1. 僅在沒有其他商業負載的專用 VM 使用。
2. 設定正確 `DOCKER_GID`，保持容器內非 root user。
3. 以防火牆限制 Worker 只可連 Redis、control-plane、LLM provider 與已授權目標。
4. 正式大規模環境改用 rootless Docker socket、Kubernetes sandbox 或 microVM Worker。
5. AD Worker 必須是不同節點，預設唯讀，不共用 Docker socket。

## Stripe

在 Stripe 建立 Professional 與 Business recurring Price，填入：

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_PROFESSIONAL`
- `STRIPE_PRICE_BUSINESS`

Webhook URL：`https://<domain>/v1/billing/webhooks/stripe`

訂閱 metadata 由 Checkout 建立為 `jysec_tenant_id` 與 `jysec_plan_id`。Enterprise 不走自助結帳，應使用合約與人工 license provisioning。

## 發布前檢查

```bash
npm --prefix platform ci
npm --prefix platform run check
npm --prefix platform audit --audit-level=high
npm --prefix platform run build
node --test web/static/js/*.test.cjs
go test ./...
```

再執行：

- 以專用 staging target 跑一個完整 Run。
- 驗證授權過期、越界 target、重複 idempotency key 與未授權角色均被拒絕。
- 驗證取消後 Worker 不再寫入 Finding／Artifact。
- 驗證 Stripe webhook 重送不會錯誤升級方案。
- 還原一次 PostgreSQL 備份，並驗證 evidence SHA-256。
- 產生 SBOM、掃描映像並以 digest 部署。
