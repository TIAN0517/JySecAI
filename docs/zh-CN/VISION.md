# 視覺分析（analyze_image）

## 概述

- **工具名**：`analyze_image`（MCP 內建）
- **行為**：讀取本地圖片 → `imaging` 縮放/JPEG 壓縮 → 呼叫獨立 **Vision** 模型 → 返回**純文字**給 Agent
- **上下文**：圖片位元組**不會**寫入對話歷史；僅路徑與文字摘要進入 Agent 上下文

## 配置（`config.yaml` → `vision`）

```yaml
vision:
  enabled: true
  model: qwen-vl-max   # 必填
  api_key:             # 留空 → 預設 AI 通道 api_key
  base_url:            # 留空 → 預設 AI 通道 base_url
  provider:            # 留空 → 預設 AI 通道 provider
  max_image_bytes: 5242880
  max_dimension: 2048
  jpeg_quality: 82
  max_payload_bytes: 524288
  skip_preprocess_below_bytes: 2097152  # 低於 2MB 且長邊<=max_dimension 時原圖直傳；0=始終 JPEG 壓縮
  detail: low          # low | high | auto
  timeout_seconds: 60
```

`enabled: false` 時不註冊工具。

## Web 設定

**系統設定 → 基本設定 → 視覺分析（analyze_image）** 可配置啟用開關、視覺模型、API Key/Base URL（留空複用預設 AI 通道）、預處理引數；**儲存並應用** 後寫入 `config.yaml` 並重新註冊 MCP 工具。

## 路徑

`analyze_image` 可讀取伺服器上任意可讀的圖片檔案路徑（絕對路徑或相對於程序工作目錄的相對路徑）。仍校驗圖片副檔名與常規檔案型別。

## Agent 使用

系統提示已說明：遇圖片呼叫 `analyze_image`，勿用 `read_file` 讀二進位制圖。

`multi_agent.eino_middleware.tool_search_always_visible_tools` 建議包含 `analyze_image`。

## 合規

啟用後圖片會發往 Vision API 配置的上游；敏感環境請使用可信閘道器或保持 `enabled: false`。
