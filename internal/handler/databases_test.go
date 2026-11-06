package handler

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"testing"

	"jysecai/internal/config"

	"github.com/gin-gonic/gin"
	_ "github.com/mattn/go-sqlite3"
)

func TestDatabasesCatalogIncludesRedirectAndLoan(t *testing.T) {
	gin.SetMode(gin.TestMode)
	dir := t.TempDir()
	mainPath := filepath.Join(dir, "main.db")
	loanPath := filepath.Join(dir, "loan_cases.db")
	mustExecSQL(t, mainPath, `
CREATE TABLE redirect_verify_runs (id TEXT);
INSERT INTO redirect_verify_runs VALUES ('a'),('b');
CREATE TABLE redirect_verify_results (id TEXT);
INSERT INTO redirect_verify_results VALUES ('r');
CREATE TABLE xss_payloads (id TEXT);
`)
	mustExecSQL(t, loanPath, `
CREATE TABLE loan_cases (case_no TEXT);
INSERT INTO loan_cases VALUES ('1'),('2'),('3');
`)

	cfg := &config.Config{}
	cfg.Database.Path = mainPath
	cfg.Redirect.URLs = []string{"https://97y.me/tjneJ"}
	attach := true
	cfg.Redirect.AttachScan = &attach

	h := NewDatabasesHandler(cfg, &LoanHandler{dbPath: loanPath}, &AssetIntelHandler{dbPath: filepath.Join(dir, "missing.db")})
	r := gin.New()
	r.GET("/api/databases", h.Catalog)
	req := httptest.NewRequest(http.MethodGet, "/api/databases", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("status %d body %s", w.Code, w.Body.String())
	}
	var out map[string]any
	if err := json.Unmarshal(w.Body.Bytes(), &out); err != nil {
		t.Fatal(err)
	}
	if out["ok"] != true {
		t.Fatalf("ok=%v", out["ok"])
	}
	dbs, _ := out["databases"].([]any)
	if len(dbs) != 5 {
		t.Fatalf("databases len=%d", len(dbs))
	}
	features, _ := out["features"].([]any)
	if len(features) < 2 {
		t.Fatalf("features len=%d", len(features))
	}
	first, _ := features[0].(map[string]any)
	if first["id"] != "redirect_verify" {
		t.Fatalf("first feature %v", first["id"])
	}
	if first["attach_scan"] != true {
		t.Fatalf("attach_scan=%v", first["attach_scan"])
	}
	counts, _ := first["counts"].(map[string]any)
	if counts["runs"] != float64(2) || counts["results"] != float64(1) {
		t.Fatalf("redirect counts %+v", counts)
	}
	loanFeat, _ := features[1].(map[string]any)
	if loanFeat["imported"] != true {
		t.Fatalf("loan imported=%v", loanFeat["imported"])
	}
}

func TestInspectSQLiteMissingFile(t *testing.T) {
	got := inspectSQLite("loan", "贷款", "x", filepath.Join(t.TempDir(), "nope.db"), "loan-cases", loanFeatureTables)
	if got.Exists {
		t.Fatal("missing file should not exist")
	}
	if got.TableCount != 0 {
		t.Fatalf("table_count=%d", got.TableCount)
	}
}

func mustExecSQL(t *testing.T, path, sqlText string) {
	t.Helper()
	db, err := sql.Open("sqlite3", path)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if _, err := db.Exec(sqlText); err != nil {
		t.Fatal(err)
	}
}
