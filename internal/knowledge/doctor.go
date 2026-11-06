package knowledge

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"jysecai/internal/config"
)

// DoctorOptions 控制一次知識庫診斷的行為。
type DoctorOptions struct {
	// ConfigPath 是要診斷的設定檔。生產環境通常是 /var/lib/jysecai/core/config.yaml。
	ConfigPath string
	// DBPath 可選。給定時會讀取索引現況，偵測「換了模型但舊向量還在」的情況。
	// 診斷一律唯讀，不會寫入。
	DBPath string
	// SkipProbe 跳過實際呼叫 embedding 端點。
	SkipProbe bool
	// Timeout 探測端點的逾時時間。
	Timeout time.Duration
}

// FindingLevel 表示一個診斷結果的嚴重度。
type FindingLevel string

const (
	LevelError FindingLevel = "錯誤"
	LevelWarn  FindingLevel = "警告"
	LevelOK    FindingLevel = "正常"
)

// Finding 是一條診斷訊息。
type Finding struct {
	Level   FindingLevel
	Message string
}

// ModelDimCount 是某個 (embedding_model, embedding_dim) 組合在索引中的筆數。
type ModelDimCount struct {
	Model string
	Dim   int
	Count int
}

// IndexState 是知識庫索引的現況。
type IndexState struct {
	Available bool
	Reason    string
	Total     int
	Items     []ModelDimCount
}

// DoctorReport 是一次完整診斷的結果。
type DoctorReport struct {
	ConfigPath string
	Enabled    bool
	BasePath   string
	Resolved   ResolvedEmbedding
	Findings   []Finding
	Probe      *EmbeddingProbeResult
	Index      *IndexState
}

// Healthy 表示沒有任何錯誤層級的診斷結果。
func (r *DoctorReport) Healthy() bool {
	for _, f := range r.Findings {
		if f.Level == LevelError {
			return false
		}
	}
	return true
}

func (r *DoctorReport) add(level FindingLevel, format string, args ...any) {
	r.Findings = append(r.Findings, Finding{Level: level, Message: fmt.Sprintf(format, args...)})
}

// RunDoctor 診斷知識庫設定、端點可達性與索引現況。
//
// 這是唯讀的：不會寫設定、不會重建索引、不會修改資料庫。
func RunDoctor(opts DoctorOptions) (*DoctorReport, error) {
	if strings.TrimSpace(opts.ConfigPath) == "" {
		return nil, fmt.Errorf("需要 --config 指定設定檔路徑")
	}
	cfg, err := config.Load(opts.ConfigPath)
	if err != nil {
		return nil, fmt.Errorf("讀取設定失敗: %w", err)
	}

	report := &DoctorReport{
		ConfigPath: opts.ConfigPath,
		Enabled:    cfg.Knowledge.Enabled,
		BasePath:   cfg.Knowledge.BasePath,
		Resolved:   ResolveEmbeddingConfig(&cfg.Knowledge, &cfg.OpenAI),
	}

	if !report.Enabled {
		report.add(LevelWarn,
			"knowledge.enabled = false，整個知識庫功能目前是關閉的；索引不會建立，檢索也不會生效")
	}
	for _, msg := range report.Resolved.Diagnostics() {
		report.add(LevelError, "%s", msg)
	}

	if !opts.SkipProbe {
		timeout := opts.Timeout
		if timeout <= 0 {
			timeout = 30 * time.Second
		}
		probe := ProbeEmbedding(&http.Client{Timeout: timeout}, report.Resolved, timeout)
		report.Probe = &probe
		applyProbeFinding(report, probe)
	}

	if strings.TrimSpace(opts.DBPath) != "" {
		report.Index = inspectIndex(opts.DBPath)
		applyIndexFinding(report, report.Index, report.Resolved)
	}

	return report, nil
}

// applyProbeFinding 把探測結果轉成診斷訊息，並針對常見 HTTP 狀態碼給出成因說明。
func applyProbeFinding(report *DoctorReport, probe EmbeddingProbeResult) {
	if probe.Err != nil {
		report.add(LevelError, "無法呼叫 embedding 端點 %s: %v", probe.Endpoint, probe.Err)
		return
	}
	switch probe.StatusCode {
	case http.StatusOK:
		report.add(LevelOK, "embedding 端點可用: HTTP 200，向量維度 %d，回應模型 %q", probe.Dim, probe.Model)
	case http.StatusNotFound:
		report.add(LevelError,
			"embedding 端點回 404：%s 沒有 /embeddings 路由。"+
				"這通常代表 base_url 指向的是聊天端點（%s）。"+
				"聊天模型不提供 embedding 能力，必須改用有 embedding 模型的端點，"+
				"或在該網關上自行實作 /v1/embeddings。",
			probe.Endpoint, report.Resolved.BaseURL)
	case http.StatusUnauthorized, http.StatusForbidden:
		report.add(LevelError, "embedding 端點回 %d：金鑰被拒絕或沒有權限", probe.StatusCode)
	case http.StatusBadRequest:
		report.add(LevelError,
			"embedding 端點回 400：路由存在但不接受這個請求，通常是 model 名稱不支援。回應：%s",
			probe.Body)
	case http.StatusTooManyRequests:
		report.add(LevelWarn, "embedding 端點回 429：速率受限，稍後重試即可")
	default:
		report.add(LevelError, "embedding 端點回 %d：%s", probe.StatusCode, probe.Body)
	}
}

// applyIndexFinding 比對索引中既有的模型與目前設定的模型。
//
// 換 embedding 模型後舊向量不能混用：維度不同會直接查不到東西，
// 維度相同則是語意空間不同，檢索結果會是垃圾。兩種情況都必須完整重建。
func applyIndexFinding(report *DoctorReport, state *IndexState, resolved ResolvedEmbedding) {
	if !state.Available {
		report.add(LevelWarn, "無法檢查索引現況: %s", state.Reason)
		return
	}
	if state.Total == 0 {
		report.add(LevelWarn, "索引是空的（knowledge_embeddings 沒有任何列），需要建立索引")
		return
	}

	for _, item := range state.Items {
		if item.Model == resolved.Model {
			report.add(LevelOK, "索引 %d 筆，向量模型 %q 與目前設定一致", state.Total, item.Model)
			continue
		}
		// 維度不同時查不到東西；維度相同則是語意空間不同、檢索結果是垃圾。
		// 兩種都必須完整重建，所以一律視為錯誤。
		report.add(LevelError,
			"索引裡有 %d 筆向量用的是 %q（維度 %d），但目前設定要的是 %q。"+
				"模型不一致時舊向量不能沿用，必須完整重建索引"+
				"（POST /api/knowledge/index?mode=full），否則檢索結果會是錯的。",
			item.Count, item.Model, item.Dim, resolved.Model)
	}
}

// inspectIndex 以唯讀模式檢查索引中的模型分佈。
func inspectIndex(dbPath string) *IndexState {
	state := &IndexState{}

	abs, err := filepath.Abs(dbPath)
	if err != nil {
		state.Reason = fmt.Sprintf("路徑無效: %v", err)
		return state
	}
	// mode=ro 保證不會寫入；immutable 避免 WAL 問題
	db, err := sql.Open("sqlite3", "file:"+abs+"?mode=ro")
	if err != nil {
		state.Reason = fmt.Sprintf("開啟失敗: %v", err)
		return state
	}
	defer db.Close()
	db.SetMaxOpenConns(1)

	var exists int
	if err := db.QueryRow(
		`SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='knowledge_embeddings'`,
	).Scan(&exists); err != nil {
		state.Reason = fmt.Sprintf("查詢失敗: %v", err)
		return state
	}
	if exists == 0 {
		state.Reason = "資料庫裡沒有 knowledge_embeddings 表，這個資料庫還沒建立知識庫結構"
		return state
	}

	state.Available = true
	rows, err := db.Query(
		`SELECT embedding_model, embedding_dim, COUNT(*) FROM knowledge_embeddings GROUP BY embedding_model, embedding_dim`,
	)
	if err != nil {
		state.Available = false
		state.Reason = fmt.Sprintf("查詢失敗: %v", err)
		return state
	}
	defer rows.Close()

	for rows.Next() {
		var item ModelDimCount
		if err := rows.Scan(&item.Model, &item.Dim, &item.Count); err != nil {
			continue
		}
		state.Items = append(state.Items, item)
		state.Total += item.Count
	}
	sort.Slice(state.Items, func(i, j int) bool { return state.Items[i].Count > state.Items[j].Count })
	return state
}

// Markdown 把診斷報告輸出成 markdown，方便直接貼進文件或 issue。
func (r *DoctorReport) Markdown() string {
	var b strings.Builder
	fmt.Fprintf(&b, "## 知識庫診斷\n\n")
	fmt.Fprintf(&b, "- 設定檔：`%s`\n", r.ConfigPath)
	fmt.Fprintf(&b, "- knowledge.enabled：`%v`\n", r.Enabled)
	fmt.Fprintf(&b, "- base_path：`%s`\n\n", r.BasePath)

	b.WriteString("### 實際生效的 embedding 設定\n\n")
	b.WriteString("| 欄位 | 值 | 來源 |\n|---|---|---|\n")
	fmt.Fprintf(&b, "| provider | %s | 設定 |\n", r.Resolved.Provider)
	fmt.Fprintf(&b, "| model | %s | %s |\n", r.Resolved.Model, sourceOf(r.Resolved.ModelInherited, "設定", "預設值"))
	fmt.Fprintf(&b, "| base_url | %s | %s |\n", r.Resolved.BaseURL, sourceOf(r.Resolved.BaseURLInherited, "設定", "⚠️ 繼承自 OpenAI 聊天設定"))
	fmt.Fprintf(&b, "| api_key | %s | %s |\n\n", maskKey(r.Resolved.APIKey), sourceOf(r.Resolved.APIKeyInherited, "設定", "⚠️ 繼承自 OpenAI 聊天設定"))

	b.WriteString("### 診斷結果\n\n")
	for _, f := range r.Findings {
		icon := "•"
		switch f.Level {
		case LevelError:
			icon = "❌"
		case LevelWarn:
			icon = "⚠️"
		case LevelOK:
			icon = "✅"
		}
		fmt.Fprintf(&b, "- %s %s\n", icon, f.Message)
	}

	if r.Index != nil && r.Index.Available {
		fmt.Fprintf(&b, "\n### 索引現況（共 %d 筆）\n\n", r.Index.Total)
		b.WriteString("| 模型 | 維度 | 筆數 |\n|---|---|---|\n")
		for _, item := range r.Index.Items {
			fmt.Fprintf(&b, "| %s | %d | %d |\n", item.Model, item.Dim, item.Count)
		}
	}

	fmt.Fprintf(&b, "\n**結論：%s**\n", map[bool]string{true: "未發現錯誤", false: "有錯誤需要處理"}[r.Healthy()])
	return b.String()
}

// jsonReport 是 --json 輸出的結構。刻意不包含 API key。
type jsonReport struct {
	ConfigPath string          `json:"config_path"`
	Enabled    bool            `json:"knowledge_enabled"`
	BasePath   string          `json:"base_path"`
	Embedding  jsonEmbedding   `json:"embedding"`
	Probe      *jsonProbe      `json:"probe,omitempty"`
	Index      *jsonIndexState `json:"index,omitempty"`
	Findings   []jsonFinding   `json:"findings"`
	Healthy    bool            `json:"healthy"`
}

type jsonEmbedding struct {
	Provider         string `json:"provider"`
	Model            string `json:"model"`
	BaseURL          string `json:"base_url"`
	APIKeyPresent    bool   `json:"api_key_present"`
	APIKeyPlaceholder bool  `json:"api_key_placeholder"`
	BaseURLInherited bool   `json:"base_url_inherited"`
	APIKeyInherited  bool   `json:"api_key_inherited"`
}

type jsonProbe struct {
	OK         bool   `json:"ok"`
	Endpoint   string `json:"endpoint"`
	StatusCode int    `json:"status_code"`
	Dim        int    `json:"dim,omitempty"`
	Model      string `json:"model,omitempty"`
	Body       string `json:"body,omitempty"`
	Error      string `json:"error,omitempty"`
}

type jsonIndexState struct {
	Available bool             `json:"available"`
	Reason    string           `json:"reason,omitempty"`
	Total     int              `json:"total"`
	Items     []ModelDimCount  `json:"items,omitempty"`
}

type jsonFinding struct {
	Level   FindingLevel `json:"level"`
	Message string       `json:"message"`
}

// JSON 輸出機器可讀的診斷結果，永遠不含完整 API key。
func (r *DoctorReport) JSON() []byte {
	out := jsonReport{
		ConfigPath: r.ConfigPath,
		Enabled:    r.Enabled,
		BasePath:   r.BasePath,
		Embedding: jsonEmbedding{
			Provider:          r.Resolved.Provider,
			Model:             r.Resolved.Model,
			BaseURL:           r.Resolved.BaseURL,
			APIKeyPresent:     r.Resolved.APIKey != "",
			APIKeyPlaceholder: r.Resolved.PlaceholderAPIKey,
			BaseURLInherited:  r.Resolved.BaseURLInherited,
			APIKeyInherited:   r.Resolved.APIKeyInherited,
		},
		Healthy: r.Healthy(),
	}
	if r.Probe != nil {
		out.Probe = &jsonProbe{
			OK:         r.Probe.OK,
			Endpoint:   r.Probe.Endpoint,
			StatusCode: r.Probe.StatusCode,
			Dim:        r.Probe.Dim,
			Model:      r.Probe.Model,
			Body:       r.Probe.Body,
		}
		if r.Probe.Err != nil {
			out.Probe.Error = r.Probe.Err.Error()
		}
	}
	if r.Index != nil {
		out.Index = &jsonIndexState{
			Available: r.Index.Available,
			Reason:    r.Index.Reason,
			Total:     r.Index.Total,
			Items:     r.Index.Items,
		}
	}
	for _, f := range r.Findings {
		out.Findings = append(out.Findings, jsonFinding{Level: f.Level, Message: f.Message})
	}
	data, err := json.MarshalIndent(out, "", "  ")
	if err != nil {
		return []byte(fmt.Sprintf(`{"error":%q}`, err.Error()))
	}
	return data
}

func sourceOf(inherited bool, direct, inheritedText string) string {	if inherited {
		return inheritedText
	}
	return direct
}

// maskKey 只顯示長度與前後綴，永遠不輸出完整金鑰。
func maskKey(key string) string {
	if key == "" {
		return "(空)"
	}
	if len(key) <= 8 {
		return fmt.Sprintf("(len=%d)", len(key))
	}
	return fmt.Sprintf("`%s…%s` (len=%d)", key[:3], key[len(key)-2:], len(key))
}
