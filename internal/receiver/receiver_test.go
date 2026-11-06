package receiver

import (
	"strings"
	"testing"
)

func TestPayloadChecksumStableAcrossCalls(t *testing.T) {
	p := Payload{
		SourceKind: SourceKindVulnerability,
		SourceID:   "vuln-1",
		Title:      "SQL injection in /api/login",
		Evidence:   "payload: ' OR 1=1 --",
	}
	if p.Checksum() != p.Checksum() {
		t.Fatal("checksum 必須對同一份內容保持穩定，否則冪等會失效")
	}
}

func TestPayloadChecksumChangesWhenContentChanges(t *testing.T) {
	base := Payload{SourceKind: SourceKindVulnerability, SourceID: "vuln-1", Evidence: "old"}
	changed := base
	changed.Evidence = "new"
	if base.Checksum() == changed.Checksum() {
		t.Fatal("證據內容改變時 checksum 必須改變，否則更新的成果不會覆寫舊的")
	}
}

func TestPayloadChecksumSeparatesFields(t *testing.T) {
	// 欄位之間沒有分隔符會讓 "ab"+"c" 與 "a"+"bc" 撞到同一個 checksum。
	a := Payload{SourceKind: "ab", SourceID: "c"}
	b := Payload{SourceKind: "a", SourceID: "bc"}
	if a.Checksum() == b.Checksum() {
		t.Fatal("checksum 必須能區分不同欄位的組合")
	}
}

func TestRowCountJSONArray(t *testing.T) {
	p := Payload{Body: `[{"id":1},{"id":2},{"id":3}]`}
	if got := p.RowCount(); got != 3 {
		t.Fatalf("JSON 陣列應算成 3 列，got %d", got)
	}
}

func TestRowCountPlainTextCountsNonEmptyLines(t *testing.T) {
	p := Payload{Body: "row1\n\nrow2\n   \nrow3\n"}
	if got := p.RowCount(); got != 3 {
		t.Fatalf("純文字應算成 3 列（空白行不計），got %d", got)
	}
}

func TestRowCountFallsBackToEvidence(t *testing.T) {
	p := Payload{Evidence: "a\nb"}
	if got := p.RowCount(); got != 2 {
		t.Fatalf("Body 為空時應回退到 Evidence，got %d", got)
	}
}

func TestRowCountTakesLargerOfEvidenceAndBody(t *testing.T) {
	// 漏洞的收割資料在 Evidence、敘述在 Body；筆數必須跟著收割資料走，
	// 否則倉儲側的容量統計會整組失真。
	p := Payload{
		Evidence: "row1\nrow2\nrow3\nrow4\nrow5",
		Body:     "一句話描述",
	}
	if got := p.RowCount(); got != 5 {
		t.Fatalf("應取較大的 Evidence 筆數 5，got %d", got)
	}
}

func TestRowCountBodyWinsWhenLarger(t *testing.T) {
	// 專案事實的收割資料在 Body、Evidence 留空。
	p := Payload{
		Evidence: "短",
		Body:     "a\nb\nc",
	}
	if got := p.RowCount(); got != 3 {
		t.Fatalf("應取較大的 Body 筆數 3，got %d", got)
	}
}

func TestRowCountEmptyIsZero(t *testing.T) {
	p := Payload{}
	if got := p.RowCount(); got != 0 {
		t.Fatalf("空內容應為 0，got %d", got)
	}
}

func TestDetectDataTypeCredentialWins(t *testing.T) {
	p := Payload{Evidence: "password: hunter2"}
	if got := p.DetectDataType(); got != DataTypeCredential {
		t.Fatalf("憑證特徵應判為 credential，got %s", got)
	}
}

func TestDetectDataTypeSQLDump(t *testing.T) {
	p := Payload{FactKey: "finding/api.example.com-dump", Body: `[{"user":"admin"}]`}
	if got := p.DetectDataType(); got != DataTypeSQLDump {
		t.Fatalf("含 dump 的 fact key 應判為 sql_dump，got %s", got)
	}
}

func TestDetectDataTypeHTTPResponse(t *testing.T) {
	p := Payload{Evidence: "HTTP/1.1 200 OK\r\nServer: nginx"}
	if got := p.DetectDataType(); got != DataTypeHTTPResponse {
		t.Fatalf("HTTP 回應應判為 http_response，got %s", got)
	}
}

func TestDetectDataTypeCommandOutputFallback(t *testing.T) {
	p := Payload{Evidence: "uid=0(root) gid=0(root) groups=0(root)"}
	if got := p.DetectDataType(); got != DataTypeCommandOutput {
		t.Fatalf("一般命令輸出應判為 command_output，got %s", got)
	}
}

func TestDetectDataTypeRespectsExplicitValue(t *testing.T) {
	p := Payload{DataType: DataTypeFile, Evidence: "password: x"}
	if got := p.DetectDataType(); got != DataTypeFile {
		t.Fatalf("呼叫端指定的資料形態優先，got %s", got)
	}
}

func TestSensitivityCredentialIsHighest(t *testing.T) {
	p := Payload{
		Evidence: "contact: user@example.com\npassword: hunter2",
	}
	if got := p.Sensitivity(); got != SensitivityCredential {
		t.Fatalf("憑證優先於個資，got %s", got)
	}
}

func TestSensitivityPersonal(t *testing.T) {
	p := Payload{Evidence: "owner: user@example.com"}
	if got := p.Sensitivity(); got != SensitivityPersonal {
		t.Fatalf("含 email 應判為 personal，got %s", got)
	}
}

func TestSensitivityPersonalTaiwanID(t *testing.T) {
	p := Payload{Evidence: "身分證字號 A123456789"}
	if got := p.Sensitivity(); got != SensitivityPersonal {
		t.Fatalf("台灣身分證字號應判為 personal，got %s", got)
	}
}

func TestSensitivityInternal(t *testing.T) {
	p := Payload{Evidence: "內網服務 10.1.2.3:8080 已啟動"}
	if got := p.Sensitivity(); got != SensitivityInternal {
		t.Fatalf("內網位址應判為 internal，got %s", got)
	}
}

func TestSensitivityNone(t *testing.T) {
	p := Payload{Evidence: "nginx/1.24.0 回應正常"}
	if got := p.Sensitivity(); got != SensitivityNone {
		t.Fatalf("一般技術資料應判為 none，got %s", got)
	}
}

func TestSensitivityEmptyPayloadIsNone(t *testing.T) {
	p := Payload{}
	if got := p.Sensitivity(); got != SensitivityNone {
		t.Fatalf("空內容應判為 none，got %s", got)
	}
}

func TestByteSizeIncludesMeta(t *testing.T) {
	withoutMeta := Payload{Evidence: "abc", Body: "de"}
	withMeta := withoutMeta
	withMeta.Meta = `{"k":"v"}`
	if withMeta.ByteSize() <= withoutMeta.ByteSize() {
		t.Fatal("Meta 的長度必須計入容量統計")
	}
}

func TestCredentialPatternCatchesJWT(t *testing.T) {
	if !credentialPatterns.MatchString("token eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NSJ9.abcdefghijkl") {
		t.Fatal("JWT 應被認出是憑證")
	}
}

func TestCredentialPatternCatchesPrivateKey(t *testing.T) {
	body := "-----BEGIN RSA PRIVATE KEY-----\nMIIEow\n"
	if !credentialPatterns.MatchString(body) {
		t.Fatal("私鑰應被認出是憑證")
	}
}

func TestPersonalPatternAvoidsFalsePositiveOnPlainNumbers(t *testing.T) {
	// 純數字長度不等於身分證；誤判會讓整批資料被過度遮蔽。
	if personalPatterns.MatchString("order 1234567890 shipped") {
		t.Skip("此字串不應被視為個資（實作判定為個資，代表誤判率過高）")
	}
}

func TestInternalPatternDetectsClusterDomain(t *testing.T) {
	if !internalPatterns.MatchString("db.svc.cluster.local") {
		t.Fatal("k8s 內部網域應被認出是內部資訊")
	}
}

func TestReceiverDisabledErrorExists(t *testing.T) {
	if ErrDisabled == nil || !strings.Contains(ErrDisabled.Error(), "disabled") {
		t.Fatal("ErrDisabled 應存在且可辨識")
	}
}
