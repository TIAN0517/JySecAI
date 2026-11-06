package handler

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// loanTestDB 回傳測試用的貸款資料庫路徑；不存在則跳過（CI 沒有資料集時不失敗）。
func loanTestDB(t *testing.T) string {
	t.Helper()
	p := os.Getenv("LOAN_DB_PATH")
	if p == "" {
		p = "data/loan_cases.db"
	}
	if _, err := os.Stat(p); err != nil {
		t.Skipf("跳過：找不到貸款資料庫 %s（先跑 scripts/import_loan_cases.py）", p)
	}
	return p
}

func loanTestRouter(t *testing.T) *gin.Engine {
	t.Helper()
	gin.SetMode(gin.TestMode)
	r := gin.New()
	h := NewLoanHandler(zap.NewNop())
	h.dbPath = loanTestDB(t)
	g := r.Group("/api/loan")
	g.GET("/summary", h.Summary)
	g.GET("/cases", h.Cases)
	g.GET("/applications", h.Applications)
	g.GET("/case/:no", h.Case)
	g.GET("/tables", h.Tables)
	g.GET("/verify", h.Verify)
	g.GET("/classification", h.Classification)
	return r
}

func doGet(t *testing.T, r *gin.Engine, path string) map[string]interface{} {
	t.Helper()
	req := httptest.NewRequest(http.MethodGet, path, nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("GET %s -> HTTP %d: %s", path, w.Code, w.Body.String())
	}
	var out map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &out); err != nil {
		t.Fatalf("GET %s 回應非 JSON: %v", path, err)
	}
	return out
}

// TestLoanSummaryMatchesManifest 確認匯入後的筆數與 manifest 記載一致。
func TestLoanSummaryMatchesManifest(t *testing.T) {
	r := loanTestRouter(t)
	sum := doGet(t, r, "/api/loan/summary")
	if ok, _ := sum["ok"].(bool); !ok {
		t.Fatalf("summary 非 ok: %v", sum)
	}
	counts, _ := sum["counts"].(map[string]interface{})
	expect := map[string]float64{
		"loan_applications":   31730,
		"loan_cases":          28678,
		"loan_amount_sources": 33630,
		"loan_table_manifest": 57,
	}
	for tbl, want := range expect {
		got, ok := counts[tbl].(float64)
		if !ok {
			t.Fatalf("counts 缺 %s：%v", tbl, counts)
		}
		if got != want {
			t.Errorf("%s = %.0f，期望 %v", tbl, got, want)
		}
	}
	years, _ := sum["years"].([]interface{})
	if len(years) < 5 {
		t.Errorf("年度統計只有 %d 筆，期望 >= 5", len(years))
	}
}

// TestLoanCasesPagination 確認案件清單可分頁且總數正確。
func TestLoanCasesPagination(t *testing.T) {
	r := loanTestRouter(t)
	out := doGet(t, r, "/api/loan/cases?page=1&page_size=10")
	items, _ := out["items"].([]interface{})
	if len(items) != 10 {
		t.Fatalf("page_size=10 卻取回 %d 筆", len(items))
	}
	total, _ := out["total"].(float64)
	if total != 28678 {
		t.Errorf("total = %.0f，期望 28678", total)
	}
	first, _ := items[0].(map[string]interface{})
	if first["case_no"] == nil || first["case_no"] == "" {
		t.Errorf("案件缺少 case_no：%v", first)
	}
}

// TestLoanCaseDetailHasAmountSources 確認單案詳情含金額來源鏈（可稽核）。
func TestLoanCaseDetailHasAmountSources(t *testing.T) {
	r := loanTestRouter(t)
	out := doGet(t, r, "/api/loan/cases?page=1&page_size=1")
	items, _ := out["items"].([]interface{})
	if len(items) == 0 {
		t.Skip("查無案件可測")
	}
	item, _ := items[0].(map[string]interface{})
	no, _ := item["case_no"].(string)
	detail := doGet(t, r, "/api/loan/case/"+no)
	sources, _ := detail["amount_sources"].([]interface{})
	if len(sources) == 0 {
		t.Errorf("案件 %s 沒有金額來源鏈：%v", no, detail)
	}
	c, _ := detail["case"].(map[string]interface{})
	if c["case_no"] != no {
		t.Errorf("詳情 case_no = %v，期望 %s", c["case_no"], no)
	}
}

// TestLoanTablesManifestHasHashes 確認 57 張來源表都帶 sha256。
func TestLoanTablesManifestHasHashes(t *testing.T) {
	r := loanTestRouter(t)
	out := doGet(t, r, "/api/loan/tables")
	items, _ := out["items"].([]interface{})
	if len(items) != 57 {
		t.Fatalf("manifest 來源表 %d 張，期望 57", len(items))
	}
	for _, it := range items {
		m, _ := it.(map[string]interface{})
		sha, _ := m["sha256"].(string)
		if len(sha) != 64 {
			t.Fatalf("來源表 %v 的 sha256 長度 %d，期望 64", m["table_name"], len(sha))
		}
	}
}

// TestLoanVerifySourceHashes 確認來源檔 sha256 覆核全數通過（資料沒被動過）。
func TestLoanVerifySourceHashes(t *testing.T) {
	r := loanTestRouter(t)
	out := doGet(t, r, "/api/loan/verify")
	checked, _ := out["checked"].(float64)
	passed, _ := out["passed"].(float64)
	if checked == 0 {
		t.Skip("來源檔不在本機，略過 sha256 覆核")
	}
	if checked != passed {
		t.Errorf("sha256 覆核 %v/%v 通過", passed, checked)
	}
	if checked != 57 {
		t.Errorf("覆核了 %.0f 張來源表，期望 57", checked)
	}
}

// TestLoanClassificationDictionary 驗證分類字典端點：
//   - 回應 ok
//   - statuses 非空，且每筆都有 code / 筆數 / 佔比 / 中文名稱 pending 標記
//   - 狀態筆數總和 == total_applications（總和守恆）
//   - cross 至少含 status_x_year
//   - dictionary_gap 有明確說明（不隱藏字典缺口）
func TestLoanClassificationDictionary(t *testing.T) {
	r := loanTestRouter(t)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/loan/classification", nil)
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200", w.Code)
	}
	var out struct {
		OK       bool  `json:"ok"`
		Total    int64 `json:"total_applications"`
		Statuses []struct {
			Code    string  `json:"code"`
			N       int64   `json:"n"`
			Pct     float64 `json:"pct"`
			CNLabel string  `json:"cn_label"`
		} `json:"statuses"`
		Cross         map[string][]map[string]interface{} `json:"cross"`
		DictionaryGap string                              `json:"dictionary_gap"`
	}
	if err := json.Unmarshal(w.Body.Bytes(), &out); err != nil {
		t.Fatalf("json: %v", err)
	}
	if !out.OK {
		t.Fatal("ok = false")
	}
	if len(out.Statuses) == 0 {
		t.Fatal("statuses 為空")
	}
	var sum int64
	for _, s := range out.Statuses {
		sum += s.N
		if s.Code == "" {
			t.Fatal("有狀態缺少 code")
		}
		if s.CNLabel == "" {
			t.Fatalf("狀態 %s 的中文名稱為空，必須明確標 pending 而非留白", s.Code)
		}
	}
	if sum != out.Total {
		t.Fatalf("狀態筆數總和 %d != total_applications %d", sum, out.Total)
	}
	if _, ok := out.Cross["status_x_year"]; !ok {
		t.Fatal("cross 缺 status_x_year")
	}
	if out.DictionaryGap == "" {
		t.Fatal("dictionary_gap 為空：字典缺口必須如實說明")
	}
	t.Logf("statuses=%d total=%d cross=%d", len(out.Statuses), out.Total, len(out.Cross))
}
