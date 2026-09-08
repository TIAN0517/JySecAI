# Attack Path Templates — 27 條偵察→利用路徑
# Source: Claude-OSINT attack paths, adapted for JySecAI
# 每條路徑 = 觸發條件 → 情報來源 → 下一跳；只讀優先，利用階段必須過 HITL

## A. 憑證洩露路徑
AP-01 公開 Git 倉庫洩露 → secret-regex 命中 → 只讀驗證 → 輪換建議報告
AP-02 CI/CD 日誌外洩 → 公開 pipeline 日誌 → 提取 token → 判定權限範圍
AP-03 .env / 配置檔外洩 → /.env /.config 命中 infra-secrets → 只讀 DB ping
AP-04 前端 JS 內嵌金鑰 → 下載 JS bundle → 匹配 saas-api-keys → 追蹤 API 用途

## B. 攻擊面收斂路徑
AP-05 子域→IP→埠收斂 → subfinder/crt.sh → httpx 探活 → nmap top-ports → 服務指紋
AP-06 證書透明歷史 → crt.sh 歷史證書 → 內部命名慣例 → 隱藏資產推測
AP-07 CDN/WAF 真實源 → 歷史 DNS → 非廣域 IP 段探測 → 直連驗證
AP-08 ASN 段映射 → WHOIS/BGP → 同組織網段 → 指紋收斂

## C. 技術棧利用路徑
AP-09 指紋→已知 CVE → tech-detect → dragon-v MCP 查 CVE/EPSS → PoC 驗證（HITL）
AP-10 管理面暴露 → 常見路徑 → 預設憑證僅試一次 → 登記即停
AP-11 API 文件洩露 → /swagger /openapi.json → 端點枚舉 → 未授權測試（HITL）
AP-12 過期元件 → 版本指紋 → EOL 判定 → 公開 exploit 對照

## D. 人員與組織路徑
AP-13 郵箱格式推斷 → 公開資料 → 格式歸一 → 僅限授權釣魚演練
AP-14 離職員工殘留 → LinkedIn/官網對照 → 殘留入口線索
AP-15 技術社群暴露 → 問題貼文還原內部棧 → 縮小指紋範圍

## E. 雲與容器路徑
AP-16 元數據端點 → 需 SSRF 落地 → 169.254.169.254 探測（HITL 必經）
AP-17 對象儲存遍歷 → S3/GCS 列舉 → 只讀列出 → 登記權限
AP-18 K8s API 匿名 → /version 匿名可達 → 只讀枚舉 → 不落地
AP-19 容器 Registry 匿名拉取 → /v2/_catalog → 映像層歷史洩露

## F. 資訊匯聚路徑
AP-20 資產測繪匯聚 → FOFA/ZoomEye/Quake/Shodan（走 proxy_pool 輪換）→ 交叉確認
AP-21 歷史漏洞關聯 → 同組織歷史披露 → 類似資產復測
AP-22 代碼片段洩露 → gist/paste → 內部邏輯還原

## G. 特殊場景路徑
AP-23 小程式/APP 洩露 → 反編譯 → 硬編碼 endpoint/key
AP-24 郵件安全記錄 → SPF/DMARC 缺失 → 域欺騙風險評估
AP-25 DNS 區域傳送 → AXFR（僅一次，命中即登記）
AP-26 遠端存取暴露 → RDP/SSH/VNC 公網 → 僅指紋不爆破
AP-27 供應鏈關聯 → 子承包商域名 → 弱資產 → 主域信任鏈評估

## 通用紀律
1. 每條路徑執行前登記 operation-state.json（階段/目標/範圍）
2. 只讀優先；任何寫操作過 hitl（config.yaml default_mode）
3. 出站請求走 proxy_pool（round_robin），命中 rate limit 立即冷卻
4. 發現即落盤 recon/<target-slug>/，報告遵循 pentest-output-standards skill
