# Embedding 404 診斷與修正建議

日期：2026-10-02。本次沒有讀取 embedding key、修改設定、呼叫外部 Gateway 或執行生產索引。

## Base URL 的確切語意

`config.example.yaml:460` 定義 `provider`、`model`、`base_url`、`api_key`；範例 base URL 是 `https://dashscope.aliyuncs.com/compatible-mode/v1`。`internal/config/config.go:2245` 的 `EmbeddingConfig` 具有相同四個欄位。provider 欄位目前沒有多提供商分派，實作固定使用 OpenAI-compatible embedder。

`internal/app/app.go:250` 與 `:2092` 在 embedding base URL 為空時繼承 `openai.base_url`，key 為空時亦繼承。`internal/knowledge/embedder.go:67` 去掉尾斜線，兩邊都沒提供 base URL 才回退到預設 API URL。Eino 依賴的 go-openai `CreateEmbeddings` 將 `/embeddings` 接在 base URL 後，不會自動補 `/v1`，也不會尋找 Gateway API 路由。

| 設定 | 實際 POST 路徑 |
|---|---|
| `https://gateway.example/v1` | `https://gateway.example/v1/embeddings` |
| `https://gateway.example/api/v1` | `https://gateway.example/api/v1/embeddings` |
| `https://gateway.example` | `https://gateway.example/embeddings` |
| 已填到 `/v1/embeddings` | 錯誤地再接 `/embeddings` |

本機 `embedder_endpoint_test.go` 使用合成 key 與 httptest server 驗證實際依賴鏈：控制台 root 導向 `/embeddings` 得 HTML 404；改成 `/compatible/v1/` 後導向 `/compatible/v1/embeddings` 並取得向量。沒有改變 runtime 行為。

## 對 404 的判斷

給定的回應是 Next.js 控制台 HTML，不是 embedding JSON；證明有效請求路由落在網頁／網頁 fallback。這強烈支持 base URL／反向代理路徑錯誤，但尚不能排除正確 API 路徑未部署、權限導向控制台或 Gateway 根本不支援 embeddings。

不能猜你的 Gateway 架構。修正應由 Gateway 擁有者確認以下三件事，再填入 `knowledge.embedding`：

1. 真正的 API origin 與 prefix，例如 `/v1` 或 `/api/v1`；填的是 prefix，不包含 `/embeddings`。
2. 該路由確實代理 embeddings，而非只支援 chat；指定 model 是供應商實際提供的 embedding model，不能假設聊天模型可產生向量。
3. 該 API 的 key 與權限。長度 10 的現有 key 不能僅由長度判定真假；需擁有者確認，不能在報告中複製。

若 Gateway 沒提供 embeddings，可由使用者選擇已確認支援的 embedding 供應商，設定独立 API base URL／model／key；這是後續選擇，沒有自動切換。

路由驗收：以供應商確認的 URL、model、合成非敏感輸入做最小 POST。預期 HTTP 200、JSON `data[0].embedding` 為數值陣列，維度與 model 一致。404 HTML 仍表示路由未對；401／403 JSON 表示到達了 API 但授權仍未解決。不要把 404 解決等同於索引完成。

## 4 筆失敗項目如何補索引

可以重試，但「4/11」只是一個中途失敗計數，不能憑它證明最終恰好剩 4 筆。`indexer.go` 在超過 30% 時記錄錯誤；五次連續失敗會提早停止，因此可能還有未嘗試項目。

`IndexItem` 先刪該 item 的舊向量，再產生嵌入。embedding HTTP 404 發生在寫入向量前，因此該 item 沒有向量會被 `runIndexMissing` 的 LEFT JOIN 再次選中；知識正文仍在，沒有永久 failed 標記阻止補索引。

管理員修正設定、讓新的 embedder 生效並通過最小 API 測試後，透過已驗證登入狀態呼叫 **`POST /api/knowledge/index?mode=missing`**（也可用既有 UI 索引操作，預設 missing）；以 **`GET /api/knowledge/index-status`** 追蹤進度與錯誤。這會補所有缺向量項目，包括失敗／未嘗試項目。若某項目有部分向量殘留，missing 不會挑中，需人工確認後另選單筆重建或 full；full 會重建全部、產生費用，而且現行流程先刪舊向量，不能隨意執行。

這次已確認可補索引的程式路徑與本機 API 路徑測試；沒有生產 API 成功證據，尚不能聲稱那 4 筆已完成。
