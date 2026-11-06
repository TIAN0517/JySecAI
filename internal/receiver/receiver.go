// Package receiver 把平台收割到的成果送到外部資料庫（目前是主力機 MySQL）。
//
// 設計紅線，全部來自實際會出事的地方：
//
//  1. 絕不拖慢或拖垮平台主寫入路徑。MySQL 掛了、網路斷了、帳號被鎖，
//     平台照常運作 —— 只是接收暫停。這是「外部接收端」和「主資料庫」的
//     根本差別，別把它做成後者。
//  2. 冪等。同一筆成果送幾次都只落地一次（以 checksum 判定），
//     否則重試會把倉儲灌成同一份資料的 N 倍。
//  3. 完整溯源。每一筆收割成果都要能回溯到：哪個專案、哪個漏洞、
//     哪次對話、什麼時間、證據是什麼。沒有溯源的收割資料在交付時等於廢紙。
//  4. 敏感度分級。收割資料常含憑證與個資，倉儲必須知道哪一批是憑證、
//     哪一批是個資，才能決定存取與遮蔽策略。
package receiver

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"regexp"
	"strings"
	"time"
)

// SourceKind 成果的來源類型。
const (
	SourceKindVulnerability = "vulnerability"
	SourceKindProjectFact   = "project_fact"
)

// DataType 收割成果的資料形態。
const (
	DataTypeUnknown       = "unknown"
	DataTypeSQLDump       = "sql_dump"
	DataTypeCommandOutput = "command_output"
	DataTypeHTTPResponse  = "http_response"
	DataTypeFile          = "file"
	DataTypeCredential    = "credential"
	DataTypeMetadata      = "metadata"
	DataTypeChain         = "attack_chain"
)

// Sensitivity 敏感度分級。
const (
	SensitivityNone       = "none"       // 一般技術資料
	SensitivityInternal   = "internal"   // 內部架構／內網資訊
	SensitivityPersonal   = "personal"   // 含個資
	SensitivityCredential = "credential" // 含憑證 —— 最高風險
)

// Payload 一次要送出的收割成果。
//
// 欄位刻意涵蓋「這是誰、在哪、什麼時候、靠哪個漏洞拿到、證據是什麼」，
// 缺任何一項，倉儲側就無法把它接回專案。
type Payload struct {
	SourceKind      string `json:"source_kind"`
	SourceID        string `json:"source_id"`
	ProjectID       string `json:"project_id"`
	ConversationID  string `json:"conversation_id"`
	VulnerabilityID string `json:"vulnerability_id"`
	FactKey         string `json:"fact_key"`
	Category        string `json:"category"`
	// TypeCode 受控分類代碼（例：sql-injection）。
	// Category 是顯示用標籤，TypeCode 是機器可讀代碼；兩者都給，
	// 倉儲側才能用代碼做維度、用標籤給人看。
	TypeCode   string `json:"type_code"`
	Title      string `json:"title"`
	Target     string `json:"target"`
	Severity   string `json:"severity"`
	Status     string `json:"status"`
	Confidence int    `json:"confidence"`
	DataType   string `json:"data_type"`
	Evidence   string `json:"evidence"`
	Body       string `json:"body"`
	// Meta 來源專屬的附加欄位（JSON 序列化後放這裡）。
	//
	// 漏洞與專案事實的欄位集合本來就不一樣（漏洞有 severity/status/confidence，
	// 事實有 confirmed/tentative/deprecated 這種字串等級）。硬塞進共用欄位
	// 只會讓其中一邊失真 —— 例如把事實的 "tentative" 硬轉成數字，
	// 倉儲側就分不出「有人工確認過」和「Agent 自己猜的」。
	// 所以多型欄位各自序列化，不共用語意。
	Meta       string    `json:"meta"`
	OccurredAt time.Time `json:"occurred_at"`
}

// Checksum 內容校驗碼。
//
// 以「來源識別 + 實際內容」計算：同一筆成果內容沒變就永遠是同一個 checksum，
// 內容變了（證據更新）就是新的 checksum，接收端據此判斷要覆寫還是跳過。
func (p Payload) Checksum() string {
	h := sha256.New()
	for _, part := range []string{
		p.SourceKind, p.SourceID, p.ProjectID, p.ConversationID, p.VulnerabilityID,
		p.FactKey, p.Category, p.TypeCode, p.Title, p.Target, p.Evidence, p.Body, p.Meta,
	} {
		h.Write([]byte(part))
		h.Write([]byte{0})
	}
	return hex.EncodeToString(h.Sum(nil))
}

// ByteSize 成果的位元組大小（估算，用於倉儲側的容量統計）。
func (p Payload) ByteSize() int64 {
	return int64(len(p.Evidence) + len(p.Body) + len(p.Title) + len(p.Meta))
}

// RowCount 估算成果的資料筆數。
//
// 收割資料最常見的兩種形態：JSON 陣列（dump 出來的 rows）或逐行文字
// （命令輸出、檔案內容）。兩者都用「實際有內容的行數」估算，
// 寧可保守低估也不要灌水 —— 倉儲側會用這個數字做容量與覆蓋率統計。
//
// 取 Evidence 與 Body 兩者中較大的筆數，而不是固定優先某一個：
// 漏洞的收割資料放在 Evidence（敘述放在 Body），專案事實的收割資料放在 Body
// （Evidence 留空）。固定優先其中一邊，就會讓另一類成果的筆數永遠是 1 ——
// 那會讓倉儲側的容量統計整組失真。
func (p Payload) RowCount() int {
	evidence := p.countDataLines(p.Evidence)
	body := p.countDataLines(p.Body)
	if body > evidence {
		return body
	}
	return evidence
}

// countDataLines 算單一文字欄位裡的資料筆數。
func (p Payload) countDataLines(text string) int {
	text = strings.TrimSpace(text)
	if text == "" {
		return 0
	}
	// JSON 陣列：數元素數。
	if strings.HasPrefix(text, "[") {
		var rows []json.RawMessage
		if err := json.Unmarshal([]byte(text), &rows); err == nil {
			return len(rows)
		}
	}
	count := 0
	for _, line := range strings.Split(text, "\n") {
		if strings.TrimSpace(line) != "" {
			count++
		}
	}
	return count
}

// DetectDataType 推測成果的資料形態。
//
// 呼叫端沒指定時才推測；推測結果只是給倉儲側做分類與統計的依據，
// 不影響證據本身，所以推測錯了不影響資料正確性。
func (p Payload) DetectDataType() string {
	if p.DataType != "" && p.DataType != DataTypeUnknown {
		return p.DataType
	}
	text := strings.TrimSpace(p.Evidence + "\n" + p.Body)
	switch {
	case text == "":
		return DataTypeUnknown
	case credentialPatterns.MatchString(text):
		return DataTypeCredential
	case strings.Contains(strings.ToLower(p.Title), "dump") ||
		strings.Contains(strings.ToLower(p.FactKey), "dump") ||
		strings.HasPrefix(text, "["):
		return DataTypeSQLDump
	case strings.Contains(strings.ToLower(text), "http/1.") ||
		strings.Contains(strings.ToLower(text), "http/2"):
		return DataTypeHTTPResponse
	case strings.Contains(strings.ToLower(p.FactKey), "metadata"):
		return DataTypeMetadata
	case strings.Contains(strings.ToLower(p.FactKey), "chain"):
		return DataTypeChain
	default:
		return DataTypeCommandOutput
	}
}

// Sensitivity 判定成果的敏感度。
//
// 判定順序有意義：憑證比個資更敏感，個資比內部資訊更敏感。
// 只要命中任何一類，就取最高的那一類 —— 混級的資料必須按最高級處理，
// 標成「無敏感」比標錯級嚴重得多。
func (p Payload) Sensitivity() string {
	text := p.Evidence + "\n" + p.Body + "\n" + p.Title + "\n" + p.Target
	if credentialPatterns.MatchString(text) {
		return SensitivityCredential
	}
	if personalPatterns.MatchString(text) {
		return SensitivityPersonal
	}
	if internalPatterns.MatchString(text) {
		return SensitivityInternal
	}
	return SensitivityNone
}

var (
	// 憑證特徵。
	credentialPatterns = regexp.MustCompile(`(?i)` +
		`-----BEGIN [A-Z ]*PRIVATE KEY-----` +
		`|\b(password|passwd|pwd|passphrase|secret|api[_-]?key|apikey|access[_-]?token|` +
		`refresh[_-]?token|client[_-]?secret|authorization)\b\s*[:=]` +
		`|\bbearer\s+[A-Za-z0-9._\-]{16,}` +
		`|\bAKIA[0-9A-Z]{16}\b` +
		`|\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.` +
		`|\bmysql\s+-[a-z]*u[a-z]*\s+[^\s]+\s+-p[^\s]+`)

	// 個資特徵。刻意保守：寧可漏判也不誤判，誤判會讓整批資料被過度遮蔽。
	personalPatterns = regexp.MustCompile(`(?i)` +
		`[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}` + // email
		`|\b[A-Z]\d{9}\b` + // 台灣身分證字號
		`|(?:\+?886|0)9\d{2}[\s\-]?\d{3}[\s\-]?\d{3}\b` + // 台灣手機號
		`|\+[1-9]\d{7,14}\b` + // E.164 電話
		`|\b(?:4\d{15}|5[1-5]\d{14}|3[47]\d{13}|6(?:011|5\d{2})\d{12})\b`) // 信用卡號

	// 內部架構特徵。
	internalPatterns = regexp.MustCompile(`(?i)` +
		`\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|` +
		`172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b` +
		`|\b[a-z0-9\-]+\.(?:internal|local|corp|lan|intranet|svc\.cluster\.local)\b` +
		`|\b(?:kubectl|docker|etcd|kubernetes|k8s)\b`)
)

// DeliveryResult 一次送出的結果。
type DeliveryResult struct {
	Delivered bool   // 實際寫入
	Skipped   bool   // 因為已經送過而跳過
	DatasetID string // 倉儲側的資料集 ID
	Reason    string
}

// Sink 外部接收端。
type Sink interface {
	// Deliver 送出一筆成果。失敗必須回 error，但呼叫端不得讓它影響主流程。
	Deliver(ctx context.Context, p Payload) (DeliveryResult, error)
	// Close 釋放資源。
	Close() error
}

// FailureRecorder 選用介面：能把送出失敗寫進接收端自己的帳本。
//
// 沒有失敗紀錄的接收端，看起來就像「從來沒有東西要送」——
// 那是最容易讓人誤判系統狀態的一種沉默。
type FailureRecorder interface {
	RecordFailure(ctx context.Context, p Payload, cause error)
}

// LedgerEntry 帳本裡的一筆紀錄。
type LedgerEntry struct {
	SourceKind string
	SourceID   string
	Checksum   string
	Status     string
	DatasetID  string
}

// LedgerPrefetcher 選用介面：能在開始交付前一次把整份帳本讀回來。
//
// 為什麼需要：Deliver 每筆都要查一次帳本（判斷內容有沒有變），
// 在跨主機的資料庫上，這個逐筆查詢就是整個匯入的瓶頸 ——
// 4359 筆就是 4359 次往返，實測每筆約 0.8 秒。
// 先一次把帳本讀進記憶體、當場比對 checksum，匯入時間從數十分鐘降到幾分鐘。
//
// 注意語意：快照是開始時的狀態。若期間有其他寫入者改了同一筆，
// 本地判斷可能與資料庫不一致 —— 送出仍然是冪等的（UPSERT），
// 最壞結果是多送一次或錯過一次「本來該更新」的資料。
type LedgerPrefetcher interface {
	LedgerSnapshot(ctx context.Context, sourceKind string) (map[string]LedgerEntry, error)
}

// ErrDisabled 接收端未啟用。
var ErrDisabled = fmt.Errorf("receiver disabled")
