package handler

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/csv"
	"encoding/hex"
	"net/http"
	"os"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// LoanHandler 提供「真實貸款案件主檔」的唯讀橋接。
//
// 資料來源：中租（chailease）mid-sign 靶站 2023–2026 完整批次匯出（57 表），
// 經 scripts/import_loan_cases.py 整理成案件主檔 v5 後匯入獨立 SQLite。
//
// 設計原則:
//   - 唯讀：只 SELECT，獨立 DB（data/loan_cases.db），不碰平台主庫
//   - 可稽核：每張來源表帶 sha256；/api/loan/verify 可重新對檔案覆核
//   - 不製造資料：沒有匯入就是空集合 + 明確的 db_missing 標記
type LoanHandler struct {
	logger *zap.Logger
	dbPath string
}

// NewLoanHandler 建立 handler。dbPath 優先讀 LOAN_DB_PATH，其次本機既有檔。
func NewLoanHandler(logger *zap.Logger) *LoanHandler {
	return &LoanHandler{logger: logger, dbPath: resolveLoanDBPath()}
}

func resolveLoanDBPath() string {
	if p := strings.TrimSpace(os.Getenv("LOAN_DB_PATH")); p != "" {
		return p
	}
	for _, p := range []string{
		"data/loan_cases.db",
		"/var/lib/jysecai/core/loan_cases.db",
		"/opt/jysecai/core/current/data/loan_cases.db",
	} {
		if fileExists(p) {
			return p
		}
	}
	return "data/loan_cases.db"
}

func (h *LoanHandler) open() (*sql.DB, bool) {
	if h.dbPath == "" || !fileExists(h.dbPath) {
		return nil, false
	}
	db, err := openSQLiteRO(h.dbPath)
	if err != nil || db == nil {
		return nil, false
	}
	return db, true
}

func (h *LoanHandler) metaMap(db *sql.DB) map[string]string {
	out := map[string]string{}
	rows, err := db.QueryContext(context.Background(), "SELECT key, value FROM loan_meta")
	if err != nil {
		return out
	}
	defer rows.Close()
	for rows.Next() {
		var k, v string
		if rows.Scan(&k, &v) == nil {
			out[k] = v
		}
	}
	return out
}

func nullStr(v sql.NullString) string {
	if v.Valid {
		return v.String
	}
	return ""
}

func nullFloat(v sql.NullFloat64) float64 {
	if v.Valid {
		return v.Float64
	}
	return 0
}

func nullInt(v sql.NullInt64) int64 {
	if v.Valid {
		return v.Int64
	}
	return 0
}

// Summary 回傳資料集總覽：來源、行數、年度分布、manifest 覆核狀態。
func (h *LoanHandler) Summary(c *gin.Context) {
	db, ok := h.open()
	if !ok {
		c.JSON(http.StatusOK, gin.H{
			"ok": false, "db_missing": true, "db_path": h.dbPath,
			"message": "貸款資料庫尚未匯入（執行 scripts/import_loan_cases.py）",
		})
		return
	}
	defer db.Close()

	meta := h.metaMap(db)

	years := []gin.H{}
	rows, err := db.QueryContext(context.Background(),
		"SELECT year, app_count, total_approved FROM loan_year_stats ORDER BY year")
	if err == nil {
		defer rows.Close()
		for rows.Next() {
			var year, apps int64
			var total sql.NullFloat64
			if rows.Scan(&year, &apps, &total) == nil {
				years = append(years, gin.H{
					"year": year, "app_count": apps, "total_approved": nullFloat(total),
				})
			}
		}
	}

	counts := gin.H{}
	for _, t := range []string{"loan_cases", "loan_applications", "loan_amount_sources",
		"loan_repay_plans", "loan_repay_plans_his", "loan_collateral_monthly",
		"loan_contract_details", "loan_table_manifest"} {
		var n int64
		if err := db.QueryRowContext(context.Background(),
			"SELECT COUNT(*) FROM "+t).Scan(&n); err == nil {
			counts[t] = n
		}
	}

	// 案件金額總計（以核准金額欄加總，僅供對照）
	var sumApproved sql.NullFloat64
	_ = db.QueryRowContext(context.Background(),
		"SELECT SUM(approved_amount) FROM loan_applications").Scan(&sumApproved)

	// 金額來源分布（案件層）
	sourceDist := []gin.H{}
	srows, err := db.QueryContext(context.Background(),
		`SELECT source_field, COUNT(*) AS cnt, SUM(amount) AS total
		 FROM loan_amount_sources GROUP BY source_field ORDER BY cnt DESC LIMIT 20`)
	if err == nil {
		defer srows.Close()
		for srows.Next() {
			var f string
			var cnt int64
			var total sql.NullFloat64
			if srows.Scan(&f, &cnt, &total) == nil {
				sourceDist = append(sourceDist, gin.H{
					"source_field": f, "cases": cnt, "total": nullFloat(total),
				})
			}
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"ok": true, "db_path": h.dbPath, "meta": meta,
		"counts": counts, "years": years,
		"sum_approved":        nullFloat(sumApproved),
		"source_distribution": sourceDist,
	})
}

// Cases 回傳案件層清單（分頁 + 篩選 + 搜尋）。
func (h *LoanHandler) Cases(c *gin.Context) {
	db, ok := h.open()
	if !ok {
		c.JSON(http.StatusOK, gin.H{"ok": false, "db_missing": true, "items": []gin.H{}, "count": 0})
		return
	}
	defer db.Close()

	page := queryInt(c, "page", 1)
	size := queryInt(c, "page_size", 50)
	if page < 1 {
		page = 1
	}
	if size < 1 || size > 500 {
		size = 50
	}
	where := []string{"1=1"}
	args := []interface{}{}
	if y := queryInt(c, "year", 0); y > 0 {
		where = append(where, "code_year = ?")
		args = append(args, y)
	}
	if q := strings.TrimSpace(c.Query("q")); q != "" {
		where = append(where, "case_no LIKE ?")
		args = append(args, "%"+q+"%")
	}
	if st := strings.TrimSpace(c.Query("source_table")); st != "" {
		where = append(where, "source_tables LIKE ?")
		args = append(args, "%"+st+"%")
	}
	cond := strings.Join(where, " AND ")

	var total int64
	if err := db.QueryRowContext(context.Background(),
		"SELECT COUNT(*) FROM loan_cases WHERE "+cond, args...).Scan(&total); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	qArgs := append(append([]interface{}{}, args...), size, (page-1)*size)
	rows, err := db.QueryContext(context.Background(),
		`SELECT case_no, app_count, first_apply_at, last_apply_at, code_year,
		        amount_source_flag, amount_source_detail, source_tables, orphan_case, master_app
		 FROM loan_cases WHERE `+cond+` ORDER BY code_year DESC, case_no LIMIT ? OFFSET ?`, qArgs...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	items := []gin.H{}
	for rows.Next() {
		var caseNo, firstAt, lastAt, flag, detail, tables, orphan, master sql.NullString
		var apps, year sql.NullInt64
		if rows.Scan(&caseNo, &apps, &firstAt, &lastAt, &year, &flag, &detail,
			&tables, &orphan, &master) != nil {
			continue
		}
		items = append(items, gin.H{
			"case_no": nullStr(caseNo), "app_count": nullInt(apps),
			"first_apply_at": nullStr(firstAt), "last_apply_at": nullStr(lastAt),
			"code_year": nullInt(year), "amount_source_flag": nullStr(flag),
			"amount_source_detail": nullStr(detail), "source_tables": nullStr(tables),
			"orphan_case": nullStr(orphan), "master_app": nullStr(master),
		})
	}

	c.JSON(http.StatusOK, gin.H{"ok": true, "page": page, "page_size": size,
		"count": len(items), "total": total, "items": items})
}

// Applications 回傳申請單層清單。
func (h *LoanHandler) Applications(c *gin.Context) {
	db, ok := h.open()
	if !ok {
		c.JSON(http.StatusOK, gin.H{"ok": false, "db_missing": true, "items": []gin.H{}, "count": 0})
		return
	}
	defer db.Close()

	page := queryInt(c, "page", 1)
	size := queryInt(c, "page_size", 50)
	if page < 1 {
		page = 1
	}
	if size < 1 || size > 500 {
		size = 50
	}
	where := []string{"1=1"}
	args := []interface{}{}
	if cn := strings.TrimSpace(c.Query("case_no")); cn != "" {
		where = append(where, "case_no = ?")
		args = append(args, cn)
	}
	if y := queryInt(c, "year", 0); y > 0 {
		where = append(where, "apply_year = ?")
		args = append(args, y)
	}
	if st := strings.TrimSpace(c.Query("status")); st != "" {
		where = append(where, "case_status = ?")
		args = append(args, st)
	}
	cond := strings.Join(where, " AND ")

	var total int64
	_ = db.QueryRowContext(context.Background(),
		"SELECT COUNT(*) FROM loan_applications WHERE "+cond, args...).Scan(&total)

	qArgs := append(append([]interface{}{}, args...), size, (page-1)*size)
	rows, err := db.QueryContext(context.Background(),
		`SELECT app_no, case_no, apply_at, code_year, apply_year, case_status, case_type,
		        customer_group, apply_amount, collateral_amount, interest, terminal_interest,
		        approved_amount, total_approved, amount_source, periods, total_amount,
		        first_due, last_due
		 FROM loan_applications WHERE `+cond+` ORDER BY apply_year DESC, app_no LIMIT ? OFFSET ?`, qArgs...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	items := []gin.H{}
	for rows.Next() {
		var appNo, caseNo, applyAt, status, ctype, cgroup, asrc, firstDue, lastDue sql.NullString
		var cy, ay, periods sql.NullInt64
		var appAmt, coll, interest, tInterest, apprv, totalApprv, totalAmt sql.NullFloat64
		if rows.Scan(&appNo, &caseNo, &applyAt, &cy, &ay, &status, &ctype, &cgroup,
			&appAmt, &coll, &interest, &tInterest, &apprv, &totalApprv, &asrc,
			&periods, &totalAmt, &firstDue, &lastDue) != nil {
			continue
		}
		items = append(items, gin.H{
			"app_no": nullStr(appNo), "case_no": nullStr(caseNo), "apply_at": nullStr(applyAt),
			"code_year": nullInt(cy), "apply_year": nullInt(ay),
			"case_status": nullStr(status), "case_type": nullStr(ctype),
			"customer_group": nullStr(cgroup), "apply_amount": nullFloat(appAmt),
			"collateral_amount": nullFloat(coll), "interest": nullFloat(interest),
			"terminal_interest": nullFloat(tInterest), "approved_amount": nullFloat(apprv),
			"total_approved": nullFloat(totalApprv), "amount_source": nullStr(asrc),
			"periods": nullInt(periods), "total_amount": nullFloat(totalAmt),
			"first_due": nullStr(firstDue), "last_due": nullStr(lastDue),
		})
	}

	c.JSON(http.StatusOK, gin.H{"ok": true, "page": page, "page_size": size,
		"count": len(items), "total": total, "items": items})
}

// Case 回傳單一案件詳情：案件層 + 金額來源鏈 + 其申請單 + 契約明細。
func (h *LoanHandler) Case(c *gin.Context) {
	no := strings.TrimSpace(c.Param("no"))
	db, ok := h.open()
	if !ok {
		c.JSON(http.StatusOK, gin.H{"ok": false, "db_missing": true})
		return
	}
	defer db.Close()

	out := gin.H{"ok": true, "case_no": no}

	var apps, year sql.NullInt64
	var firstAt, lastAt, flag, detail, tables, orphan, master sql.NullString
	err := db.QueryRowContext(context.Background(),
		`SELECT app_count, first_apply_at, last_apply_at, code_year, amount_source_flag,
		        amount_source_detail, source_tables, orphan_case, master_app
		 FROM loan_cases WHERE case_no = ?`, no).
		Scan(&apps, &firstAt, &lastAt, &year, &flag, &detail, &tables, &orphan, &master)
	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"ok": false, "message": "查無此案件"})
		return
	}
	out["case"] = gin.H{
		"case_no": no, "app_count": nullInt(apps), "first_apply_at": nullStr(firstAt),
		"last_apply_at": nullStr(lastAt), "code_year": nullInt(year),
		"amount_source_flag": nullStr(flag), "amount_source_detail": nullStr(detail),
		"source_tables": nullStr(tables), "orphan_case": nullStr(orphan),
		"master_app": nullStr(master),
	}

	sources := []gin.H{}
	srows, _ := db.QueryContext(context.Background(),
		"SELECT source_field, amount, level FROM loan_amount_sources WHERE case_no = ? ORDER BY id", no)
	if srows != nil {
		defer srows.Close()
		for srows.Next() {
			var f, lvl sql.NullString
			var amt sql.NullFloat64
			if srows.Scan(&f, &amt, &lvl) == nil {
				sources = append(sources, gin.H{"source_field": nullStr(f),
					"amount": nullFloat(amt), "level": nullStr(lvl)})
			}
		}
	}
	out["amount_sources"] = sources

	appsRows := []gin.H{}
	arows, _ := db.QueryContext(context.Background(),
		`SELECT app_no, apply_at, case_status, case_type, approved_amount, total_approved,
		        amount_source, periods, total_amount, first_due, last_due
		 FROM loan_applications WHERE case_no = ? ORDER BY app_no`, no)
	if arows != nil {
		defer arows.Close()
		for arows.Next() {
			var appNo, applyAt, status, ctype, asrc, fd, ld sql.NullString
			var apprv, tapprv, tamt sql.NullFloat64
			var periods sql.NullInt64
			if arows.Scan(&appNo, &applyAt, &status, &ctype, &apprv, &tapprv, &asrc,
				&periods, &tamt, &fd, &ld) == nil {
				appsRows = append(appsRows, gin.H{
					"app_no": nullStr(appNo), "apply_at": nullStr(applyAt),
					"case_status": nullStr(status), "case_type": nullStr(ctype),
					"approved_amount": nullFloat(apprv), "total_approved": nullFloat(tapprv),
					"amount_source": nullStr(asrc), "periods": nullInt(periods),
					"total_amount": nullFloat(tamt), "first_due": nullStr(fd),
					"last_due": nullStr(ld),
				})
			}
		}
	}
	out["applications"] = appsRows

	contracts := []gin.H{}
	crows, _ := db.QueryContext(context.Background(),
		`SELECT maj_seq_id, flw_id, stg_id, case_no, apply_dt, apprv_amt
		 FROM loan_contract_details WHERE case_no = ? LIMIT 200`, no)
	if crows != nil {
		defer crows.Close()
		for crows.Next() {
			var maj, flw, stg, cn, adt sql.NullString
			var amt sql.NullFloat64
			if crows.Scan(&maj, &flw, &stg, &cn, &adt, &amt) == nil {
				contracts = append(contracts, gin.H{"maj_seq_id": nullStr(maj),
					"flw_id": nullStr(flw), "stg_id": nullStr(stg), "case_no": nullStr(cn),
					"apply_dt": nullStr(adt), "apprv_amt": nullFloat(amt)})
			}
		}
	}
	out["contracts"] = contracts

	c.JSON(http.StatusOK, out)
}

// Tables 回傳 57 張來源表的 manifest（名稱 / 行數 / 檔案 / sha256）。
func (h *LoanHandler) Tables(c *gin.Context) {
	db, ok := h.open()
	if !ok {
		c.JSON(http.StatusOK, gin.H{"ok": false, "db_missing": true, "items": []gin.H{}})
		return
	}
	defer db.Close()

	rows, err := db.QueryContext(context.Background(),
		"SELECT table_name, rows, file, sha256 FROM loan_table_manifest ORDER BY table_name")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	items := []gin.H{}
	for rows.Next() {
		var name, file, sha sql.NullString
		var n sql.NullInt64
		if rows.Scan(&name, &n, &file, &sha) == nil {
			items = append(items, gin.H{"table_name": nullStr(name), "rows": nullInt(n),
				"file": nullStr(file), "sha256": nullStr(sha)})
		}
	}
	meta := h.metaMap(db)
	c.JSON(http.StatusOK, gin.H{"ok": true, "count": len(items), "items": items,
		"verified": meta["source_sha256_verified"], "meta": meta})
}

// Verify 重新對來源檔算 sha256 並與 manifest 比對（稽核用）。
func (h *LoanHandler) Verify(c *gin.Context) {
	db, ok := h.open()
	if !ok {
		c.JSON(http.StatusOK, gin.H{"ok": false, "db_missing": true})
		return
	}
	defer db.Close()

	meta := h.metaMap(db)
	srcDir := meta["source_dir"]
	rows, err := db.QueryContext(context.Background(),
		"SELECT table_name, file, sha256 FROM loan_table_manifest ORDER BY table_name")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	items := []gin.H{}
	okCount, checked := 0, 0
	for rows.Next() {
		var name, file, sha sql.NullString
		if rows.Scan(&name, &file, &sha) != nil {
			continue
		}
		item := gin.H{"table_name": nullStr(name), "file": nullStr(file), "sha256": nullStr(sha)}
		if srcDir != "" && file.Valid && file.String != "" {
			p := srcDir + "/" + file.String
			if _, err := os.Stat(p); err != nil {
				p = srcDir + "/csv/" + name.String
			}
			if _, err := os.Stat(p); err == nil {
				actual, err := fileSHA256(p)
				checked++
				match := err == nil && actual == sha.String
				if match {
					okCount++
				}
				item["verified"] = match
				item["actual_sha256"] = actual
			} else {
				item["verified"] = nil
				item["note"] = "來源檔不在本機，未覆核"
			}
		}
		items = append(items, item)
	}
	c.JSON(http.StatusOK, gin.H{"ok": true, "checked": checked, "passed": okCount,
		"source_dir": srcDir, "items": items})
}

// Export 匯出案件層 CSV。
func (h *LoanHandler) Export(c *gin.Context) {
	db, ok := h.open()
	if !ok {
		c.JSON(http.StatusOK, gin.H{"ok": false, "db_missing": true})
		return
	}
	defer db.Close()

	c.Header("Content-Type", "text/csv; charset=utf-8")
	c.Header("Content-Disposition", `attachment; filename="loan_cases.csv"`)
	c.Status(http.StatusOK)

	w := csv.NewWriter(c.Writer)
	_ = w.Write([]string{"案件編號", "申請單數", "申請日最早", "申請日最晚", "編碼年",
		"金額來源標記", "金額來來源明細", "來源表", "孤兒案件", "主表申請單"})
	rows, err := db.QueryContext(context.Background(),
		`SELECT case_no, app_count, first_apply_at, last_apply_at, code_year,
		        amount_source_flag, amount_source_detail, source_tables, orphan_case, master_app
		 FROM loan_cases ORDER BY code_year DESC, case_no`)
	if err != nil {
		return
	}
	defer rows.Close()
	for rows.Next() {
		var caseNo, firstAt, lastAt, flag, detail, tables, orphan, master sql.NullString
		var apps, year sql.NullInt64
		if rows.Scan(&caseNo, &apps, &firstAt, &lastAt, &year, &flag, &detail,
			&tables, &orphan, &master) != nil {
			continue
		}
		_ = w.Write([]string{
			nullStr(caseNo), strconv.FormatInt(nullInt(apps), 10), nullStr(firstAt),
			nullStr(lastAt), strconv.FormatInt(nullInt(year), 10), nullStr(flag),
			nullStr(detail), nullStr(tables), nullStr(orphan), nullStr(master),
		})
	}
	w.Flush()
}

// fileSHA256 計算檔案 sha256（十六進位小寫）。
func fileSHA256(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()
	h := sha256.New()
	buf := make([]byte, 1<<20)
	for {
		n, err := f.Read(buf)
		if n > 0 {
			h.Write(buf[:n])
		}
		if err != nil {
			break
		}
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

// ---------------------------------------------------------------- 分類字典

// crossTab 兩維交叉統計（欄名為程式內固定字串，非使用者輸入）。
func (h *LoanHandler) crossTab(ctx context.Context, db *sql.DB, colA, colB string) ([]gin.H, error) {
	sqlText := "SELECT COALESCE(NULLIF(" + colA + ",''),'(空)') AS a, " +
		"COALESCE(NULLIF(" + colB + ",''),'(空)') AS b, COUNT(*) AS n, " +
		"SUM(COALESCE(approved_amount,0)) AS amt " +
		"FROM loan_applications GROUP BY a, b ORDER BY n DESC"
	rows, err := db.QueryContext(ctx, sqlText)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := []gin.H{}
	for rows.Next() {
		var a, b sql.NullString
		var n sql.NullInt64
		var amt sql.NullFloat64
		if rows.Scan(&a, &b, &n, &amt) == nil {
			items = append(items, gin.H{"a": nullStr(a), "b": nullStr(b),
				"n": nullInt(n), "amt": int64(amt.Float64)})
		}
	}
	return items, rows.Err()
}

// Classification 回傳案件分類字典與交叉統計。
//
// 誠實邊界（重要）：
// APR_CASE_STAT / APR_CASE_TYPE / APR_CUST_LEVEL / C01_CASE_STAT 的**中文名稱**
// 在中租同站點的離線資料中不存在（57 表全為英文欄名、值為代碼）。
// 因此本端點只回傳「資料可推得特徵」＋各維度筆數／金額，
// 中文名稱一律標 pending，不臆測、不硬湊。
func (h *LoanHandler) Classification(c *gin.Context) {
	db, ok := h.open()
	if !ok {
		c.JSON(http.StatusOK, gin.H{"ok": false, "db_missing": true})
		return
	}
	defer db.Close()
	ctx := context.Background()

	const pending = "待補（同站點離線資料無中文字典）"

	// ---- 狀態字典
	statusRows, err := db.QueryContext(ctx, `
		SELECT COALESCE(NULLIF(a.case_status,''),'(空)') AS st,
		       COUNT(*) AS n,
		       SUM(COALESCE(a.approved_amount,0)) AS amt,
		       SUM(CASE WHEN p.app_no IS NULL THEN 0 ELSE 1 END) AS with_plan,
		       ROUND(AVG(COALESCE(p.periods,0)),1) AS avg_periods,
		       MIN(a.apply_year) AS y0, MAX(a.apply_year) AS y1
		FROM loan_applications a
		LEFT JOIN loan_repay_plans p ON p.app_no = a.app_no
		GROUP BY st ORDER BY n DESC`)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer statusRows.Close()

	statuses := []gin.H{}
	var totalN int64
	for statusRows.Next() {
		var st, y0, y1 sql.NullString
		var n, withPlan sql.NullInt64
		var amt, avgPeriods sql.NullFloat64
		if statusRows.Scan(&st, &n, &amt, &withPlan, &avgPeriods, &y0, &y1) != nil {
			continue
		}
		totalN += nullInt(n)
		statuses = append(statuses, gin.H{
			"code": nullStr(st), "n": nullInt(n), "amt": int64(amt.Float64),
			"with_plan": nullInt(withPlan), "avg_periods": avgPeriods.Float64,
			"year_from": nullStr(y0), "year_to": nullStr(y1),
			"cn_label": pending,
		})
	}
	// 佔比
	for _, s := range statuses {
		n := s["n"].(int64)
		pct := 0.0
		if totalN > 0 {
			pct = float64(n) * 100.0 / float64(totalN)
		}
		s["pct"] = pct
	}

	// ---- 類型 / 客群
	dicts := map[string][]gin.H{}
	for key, col := range map[string]string{"case_type": "case_type",
		"customer_group": "customer_group"} {
		rows, err := db.QueryContext(ctx,
			"SELECT COALESCE(NULLIF("+col+",''),'(空)') AS v, COUNT(*) AS n, "+
				"SUM(COALESCE(approved_amount,0)) AS amt "+
				"FROM loan_applications GROUP BY v ORDER BY n DESC")
		if err != nil {
			continue
		}
		items := []gin.H{}
		for rows.Next() {
			var v sql.NullString
			var n sql.NullInt64
			var amt sql.NullFloat64
			if rows.Scan(&v, &n, &amt) == nil {
				items = append(items, gin.H{"code": nullStr(v), "n": nullInt(n),
					"amt": int64(amt.Float64), "cn_label": pending})
			}
		}
		rows.Close()
		dicts[key] = items
	}

	// ---- 交叉統計
	cross := map[string][]gin.H{}
	for key, pair := range map[string][2]string{
		"status_x_year":  {"case_status", "code_year"},
		"status_x_type":  {"case_status", "case_type"},
		"group_x_status": {"customer_group", "case_status"},
		"amount_x_year":  {"amount_source", "code_year"},
		"type_x_year":    {"case_type", "code_year"},
	} {
		items, err := h.crossTab(ctx, db, pair[0], pair[1])
		if err != nil {
			continue
		}
		cross[key] = items
	}

	meta := h.metaMap(db)
	c.JSON(http.StatusOK, gin.H{
		"ok":                 true,
		"total_applications": totalN,
		"statuses":           statuses,
		"dicts":              dicts,
		"cross":              cross,
		"meta":               meta,
		"provenance_note": "資料來自本機既有匯出檔（" + meta["source_dir"] + "）經 import_loan_cases.py 匯入；" +
			"sha256 校驗證明匯入後與來源檔一致，**不代表**本次線上直拉。",
		"dictionary_gap": "狀態／類型／客群中文名稱在中租同站點離線資料中不存在，" +
			"本端點只回傳資料可推得特徵與統計，中文名稱標 pending。",
	})
}
