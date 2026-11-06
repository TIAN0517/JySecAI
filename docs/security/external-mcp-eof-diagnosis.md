# External MCP initialize EOF 診斷

日期：2026-10-02。本次做來源與協定分析，沒有啟動外部工具、發送工具呼叫、修改註冊資料或生產設定。

## 已知與無法確定的部分

使用者已確認舊／新 binary 都出現相同五個 initialize EOF，且 REST health 200；據此不能歸咎本次部署。EOF 僅表示 initialize 回應前通道結束，不能單憑錯誤字串判定 HTTP／SSE 版本不相容。

工作區設定與所述生產註冊名單不同：本機 `vuln-intel`／`redteam-knowledge` 的 command 是 Windows Python 路徑，没有看到其 HTTP URL；另三個生產名稱沒有出現在根設定的 server 清單。本機設定不能當成生產註冊資料，更不能直接拿來改生產。

## 從程式確認的 transport 語意

`ExternalMCPServerConfig.GetTransportType`（`internal/config/config.go:1527`）優先使用明示 `type`；未指定時，有 command 為 stdio，只有 URL 為 http。此處 http **明確表示 Streamable HTTP MCP**，不是任意 REST API，也不會自動探測舊式 SSE。

`internal/mcp/client_sdk.go:393`：stdio 使用官方 SDK CommandTransport；sse 使用 SSEClientTransport；http 使用 StreamableClientTransport。SSE 客戶端沒有整體 HTTP timeout，避免長流被 client timeout 切斷。stdio 現行使用 `exec.Command`，沒有連線 context 完成後立刻殺掉子程序的 `CommandContext` 問題。

本機兩個 read-only 資訊服務 `mcp-servers/vuln_intel/mcp_vuln_intel.py:494`、`mcp-servers/redteam_knowledge/mcp_redteam_knowledge.py:439` 都明示 `app.run(transport="stdio")`。如果生產亦註冊這些脚本，HTTP health 檢查與它們的 stdin/stdout initialize 通道不是同一條連線。

## 優先診斷順序

| 實際 transport | 應收集的證據 | 修正方向 |
|---|---|---|
| stdio | 子程序退出碼、遮蔽後的 stderr、實際 runtime／script 是否存在、MCP SDK 版本、工作目錄與服務帳號的依賴環境 | 先判斷是啟動／import 失敗，或 stdout 混入非協定文字。不要只因 EOF 就把 transport 改成 HTTP。 |
| Streamable HTTP | 實際註冊 URL、initialize HTTP status、Content-Type、JSON-RPC 回應或 SSE 事件是否完整、代理是否提前關閉 | 對照服務宣告的 MCP 路由與 transport，檢查代理 buffering／timeout、認證回應與版本協商。 |
| 舊 SSE | GET 是否取得持續的 `text/event-stream`，是否發布 endpoint 事件，後續 POST 是否回傳 initialize | 核對服務真的使用舊 SSE，以及客戶端 type 是否符合。普通 REST health 不能證明此鏈正常。 |

若認證不符，通常應能取得 401／403 或明確的子程序錯誤；若代理或 wrapper 靜默關閉，也可能只留下 EOF。需觀察實際 status／stderr，不能先猜認證 header。不得在診斷輸出複製 header 值、env 值或 URL 內的 token。

管理員應提供五個 server 的**非秘密 metadata**：name、type、URL 的 scheme/host/path（移除 userinfo/query）、runtime 類型與退出碼、遮蔽 stderr、initialize 前後的 status／Content-Type。這是釐清根因所缺的最小證據；不需要任何憑證值。

## 結論

最先要區分「stdio 子程序提早退出」與「HTTP/SSE 路由不相容」。兩個本機資訊服務的明確 stdio 實作，使「全部五個都是 HTTP/SSE 版本問題」目前没有證據。kali／hexstrike 的 health 200 只證明其 REST health 路由可用，不能驗證 MCP server／wrapper，也不能把 health URL 當成 MCP URL。

72 筆 tool_execution 證明工具執行曾成功，但單憑筆數不能證明每一筆繞過 External MCP；需按記錄的 server/source 路由核對。依使用者現況評估，平台核心不依賴這五條失敗路徑，維持低優先度。本報告完成通道與錯誤證據分析；五個生產服務的最終根因仍待上述非秘密 metadata。
