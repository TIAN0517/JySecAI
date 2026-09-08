# 貢獻規範

[English](../en-US/contributing-guide.md)

本文定義向 JySecAI 增加功能、介面、工具、前端頁面或文件時的基本要求。

## 總原則

- 新功能要有文件入口。
- 新 API 要更新 OpenAPI。
- 新前端文案要補中英文 i18n。
- 新配置要說明是否支援熱應用。
- 新高風險工具要說明 HITL 策略。
- 新資料庫欄位要相容舊庫。
- 新長任務要有狀態、取消或恢復策略。

## 新增 API Checklist

- Handler 引數校驗明確。
- 錯誤響應包含穩定 `error` 和可讀 `message`。
- 介面受認證保護，除非明確是平臺回撥。
- 修改類介面寫審計。
- 長任務寫監控或任務狀態。
- 更新 `internal/handler/openapi.go`。
- 更新 API 文件或 Recipe。
- 增加 Handler 測試。

## 新增配置 Checklist

- `config.Config` 結構體有欄位。
- `config.yaml` 示例有註釋。
- 省略欄位時有安全預設值。
- 舊配置能啟動。
- 說明是否熱應用。
- Web 設定頁不會誤刪未知欄位。
- 如影響高風險能力，更新安全文件。

## 新增工具 Checklist

適用於 YAML 工具和 Go 內建 MCP 工具。

- 工具名穩定、具體、避免重名。
- `short_description` 能被 `tool_search` 搜到。
- 輸入 schema 明確，不用裸 `cmd` 包所有行為。
- 輸出可讀且結構穩定。
- 超時和錯誤路徑可控。
- 高風險操作不進全域性白名單。
- 文件說明使用場景和風險。

## 新增前端頁面 Checklist

- 複用現有 `apiFetch`、modal、通知和狀態樣式。
- 所有可見文案補 `zh-CN.json` 和 `en-US.json`。
- 有 loading、empty、error 狀態。
- 刪除/高風險操作有確認。
- 長文字和英文按鈕不溢位。
- 瀏覽器控制檯無錯誤。

## 新增資料庫變更 Checklist

- 遷移冪等。
- 舊庫可升級。
- 欄位預設值合理。
- 大表索引謹慎。
- 測試空庫和舊庫。
- 釋出說明提醒備份。

## 新增高風險能力 Checklist

高風險包括：Shell、WebShell、C2、外部 MCP 寫入/執行、憑證訪問、批次掃描。

必須回答：

- 誰能呼叫？
- 是否需要 HITL？
- 審計記錄什麼？
- 如何取消？
- 如何清理？
- 如何禁用？
- 預設是否關閉？

## 文件要求

每個重要功能至少補：

- 用途。
- 配置。
- 操作流程。
- 風險邊界。
- 排錯。
- 原始碼錨點。

中英文文件要保持檔名一致，分別放在：

```text
docs/zh-CN/
docs/en-US/
```

更新導航：

- `docs/README.md`
- `docs/zh-CN/README.md`
- `docs/en-US/README.md`

提交文件變更前執行：

```bash
python3 scripts/check-docs.py
```

該檢查會驗證本地連結、程式碼塊閉合、中英文檔名對齊、語言導航覆蓋率，以及根 README 中的 Go 版本是否與 `go.mod` 一致。版本化示例應儘量從 `go.mod`、`config.example.yaml` 等權威檔案派生，避免手工同步。

當文件、`go.mod` 或檢查指令碼變更時，GitHub Actions 中的 `Documentation` 工作流會自動執行同一條命令。

## Review 關注點

程式碼評審優先看：

- 行為迴歸。
- 安全邊界。
- 舊資料相容。
- 錯誤處理。
- 測試缺口。
- 文件和 OpenAPI 是否同步。
