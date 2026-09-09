package sentinel

import "time"

// ScanSnapshot 表示一次完整的暴露面探測快照結果
type ScanSnapshot struct {
	ID         string         `json:"id"`
	Target     string         `json:"target"`
	TargetKind string         `json:"target_kind"` // "domain" | "ipv4"
	CreatedAt  time.Time      `json:"created_at"`
	FinishedAt string         `json:"finishedAt"` // ISO 8601 字符串
	DurationMs int64          `json:"duration_ms"`
	Status     string         `json:"status"` // "running" | "completed" | "failed"
	Error      string         `json:"error,omitempty"`
	Summary    ScanSummary    `json:"summary"`
	Assets     []AssetItem    `json:"assets"`
	Ports      []PortItem     `json:"ports"`
	Databases  []DatabaseItem `json:"databases"`
	Endpoints  []EndpointItem `json:"endpoints"`
	Findings   []FindingItem  `json:"findings"`
}

// ScanSummary 統計摘要指標
type ScanSummary struct {
	HostCount     int `json:"hostCount"`
	AliveCount    int `json:"aliveCount"`
	OpenPortCount int `json:"openPortCount"`
	EndpointCount int `json:"endpointCount"`
	LoginCount    int `json:"loginCount"`
	DatabaseCount int `json:"databaseCount"`
	HighCount     int `json:"highCount"`
	MediumCount   int `json:"mediumCount"`
	LowCount      int `json:"lowCount"`
	InfoCount     int `json:"infoCount"`
}

// AssetItem 發現的在線/離線資產主機
type AssetItem struct {
	ID       string `json:"id"`
	Host     string `json:"host"`
	Scope    string `json:"scope"` // "official" (主域) | "product" (業務) | "related" (子域)
	IP       string `json:"ip"`    // 解析 IP，空為 "無解析"
	Alive    bool   `json:"alive"`
	TLSValid bool   `json:"tlsValid"`
	Title    string `json:"title,omitempty"`
}

// PortItem 開放端口項
type PortItem struct {
	ID      string `json:"id"`
	Host    string `json:"host"`
	IP      string `json:"ip"`
	Port    int    `json:"port"`
	Service string `json:"service"`
	Banner  string `json:"banner,omitempty"`
}

// DatabaseItem 數據庫暴露項
type DatabaseItem struct {
	ID         string `json:"id"`
	EngineID   string `json:"engineId"`
	EngineName string `json:"engineName"`
	Host       string `json:"host"`
	Port       int    `json:"port"`
	Risk       string `json:"risk"` // "unauth" (未授權 - high) | "identified" (握手暴露 - medium) | "open" (端口開放 - medium)
	Evidence   string `json:"evidence"`
}

// EndpointItem 探測命中的路徑/接口項
type EndpointItem struct {
	ID          string   `json:"id"`
	URL         string   `json:"url"`
	Status      int      `json:"status"`
	Tags        []string `json:"tags"` // "login", "test", "sample", "api", "captcha", etc.
	SPAFallback bool     `json:"spaFallback"`
	Title       string   `json:"title,omitempty"`
	Snippet     string   `json:"snippet,omitempty"`
	Error       string   `json:"error,omitempty"`
}

// FindingItem 聚合風險發現項
type FindingItem struct {
	ID       string `json:"id"`
	Severity string `json:"severity"` // "high" | "medium" | "low" | "info"
	Category string `json:"category"` // "login" | "test" | "sample" | "database" | "tls" | "port" | "storage" | "api" | "other"
	Host     string `json:"host"`
	Title    string `json:"title"`
	Detail   string `json:"detail"`
	URL      string `json:"url,omitempty"`
}
