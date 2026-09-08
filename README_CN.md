# JySecAI 中文說明

完整繁體中文專案說明請見 [README.md](README.md)。

## 目前狀態

本倉庫包含兩套後端應用，reference Compose 已透過同源 Gateway 組裝。`Dockerfile.core` 用於建置 Go core，`deploy/nginx.conf` 定義公開路由：

- `/`：完整 Go 主控臺，包含專案、對話、Agent、工作流、資產、漏洞、知識庫、Blackboard、攻擊鏈、HITL、RBAC、Audit、MCP、WebShell 與 C2。
- `/governance/`：TypeScript 治理控制面，包含 Run、Scope、審批、方案額度、事件、證據 metadata、Worker queue 與選配 Stripe。
- `/assets/*`、`/v1/*` 與 `/metrics`：轉送至 TypeScript 控制面；`/metrics` 仍需 metrics token。
- `/internal/*`：不對外公開，Gateway 回覆 `404`；Worker callback 只走 Compose 私有網路。

執行 `docker compose -f compose.jysec.yml up -d --build` 後，Go core、TypeScript control-plane、Nginx Gateway、PostgreSQL 與 Redis 會一同啟動，產品入口位於 `http://127.0.0.1:8787`。Gateway 已統一路由，但尚未統一兩套身份；Go 主控臺 session 與治理控制面的 JWT／JWKS 仍彼此獨立，正式單一登入仍需共同 IdP 或 token exchange。

Worker 是選配 Compose profile，只會在執行 `docker compose -f compose.jysec.yml --profile worker up -d --build worker` 時啟動。

## 引擎邊界

- Strix CLI Driver 已實作，但必須另行啟用 Worker、LLM 與 Docker sandbox。
- Jy Workflow Driver 已實作，Compose 已包含 Go 核心，但仍須配置 service token。
- Promptfoo、PyRIT、Giskard、ART、Humanbound 與 AD Audit 目前只有 Adapter 契約；本倉庫未附相應服務或映像。
- Artifact 目前只儲存 metadata；S3／MinIO、KMS、上傳與下載尚未完成。
- Reference Compose 是單節點範例；外部 Adapter service、負載平衡、多副本協調、PostgreSQL／Redis HA、備份還原與跨區域容錯均未隨倉庫完成或部署。

## 檔案

- [系統架構與完成度](docs/jysec-architecture.md)
- [目前部署方式與生產缺口](docs/jysec-deployment.md)
- [引擎 Adapter 契約](docs/jysec-adapter-contract.md)
- [既有完整功能檔案索引](docs/README.md)
- [商用與授權邊界](COMMERCIAL.md)

本分支由 Jy 技術團隊維護。既有檔案內仍可能出現 JySecAI 名稱；品牌與檔案整併仍在進行中。
