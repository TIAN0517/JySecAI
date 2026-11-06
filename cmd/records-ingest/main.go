// Command records-ingest 把提取出來的記錄寫進平台的提取記錄庫（自動去重）。
//
// 兩種來源：
//
//	# 1) 一般 payload（掃描器 / 代理直接吐出的 JSON）
//	records-ingest --db /var/lib/jysecai/core/extracted_records.db \
//	    --payload /tmp/extract.json
//
//	# 2) 從既有 SQLite 匯入（把貸款主檔這類真實批次搬進來）
//	records-ingest --db ... --type loan_case --dataset chailease \
//	    --source import_loan_cases.py \
//	    --sqlite /var/lib/jysecai/core/loan_cases.db \
//	    --sql "SELECT case_no, apply_at, approved_amount FROM loan_applications" \
//	    --map map.json --title-col case_no
//
// map.json 是「記錄欄位 → 來源欄位」的對應：{"case_no": "case_no", "amount": "approved_amount"}
//
// 去重由資料庫的 UNIQUE(type_id, dataset, dedupe_key) 保證：同一筆資料重複匯入
// 只會更新欄位與命中次數，不會產生第二列。
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	_ "github.com/mattn/go-sqlite3"

	"jysecai/internal/records"
)

func main() {
	var (
		dbPath   = flag.String("db", "/var/lib/jysecai/core/extracted_records.db", "提取記錄庫路徑")
		payload  = flag.String("payload", "", "payload JSON 檔（與 POST /api/records/ingest 相同格式）")
		typeID   = flag.String("type", "", "型別 id（payload 模式不需要）")
		dataset  = flag.String("dataset", "", "資料集名稱")
		source   = flag.String("source", "", "來源標記（工具名／匯入腳本）")
		sqlite   = flag.String("sqlite", "", "來源 SQLite 檔")
		sqlText  = flag.String("sql", "", "來源 SELECT 語句")
		mapFile  = flag.String("map", "", "欄位對應 JSON：{記錄欄位: 來源欄位}")
		titleCol = flag.String("title-col", "", "當作標題的來源欄位")
		batch    = flag.Int("batch", 1000, "每批寫入筆數")
	)
	flag.Parse()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Minute)
	defer cancel()

	store, err := records.Open(*dbPath)
	if err != nil {
		fatal("無法開啟記錄庫: %v", err)
	}
	defer store.Close()

	var in records.IngestInput
	switch {
	case *payload != "":
		raw, err := os.ReadFile(*payload)
		if err != nil {
			fatal("讀取 payload 失敗: %v", err)
		}
		if err := json.Unmarshal(raw, &in); err != nil {
			fatal("解析 payload 失敗: %v", err)
		}
	case *sqlite != "" && *sqlText != "":
		in.TypeID = *typeID
		in.Dataset = *dataset
		in.Source = *source
		recs, err := importFromSQLite(ctx, *sqlite, *sqlText, *mapFile, *titleCol)
		if err != nil {
			fatal("匯入來源 SQLite 失敗: %v", err)
		}
		in.Records = recs
	default:
		fatal("需要 --payload 或 (--sqlite 與 --sql)")
	}

	if strings.TrimSpace(in.TypeID) == "" {
		fatal("缺少 type")
	}
	if strings.TrimSpace(in.Source) == "" {
		in.Source = "records-ingest"
	}

	total := 0
	inserted, updated := 0, 0
	// 分批寫入，避免單一交易塞太多列。
	for start := 0; start < len(in.Records); start += *batch {
		end := start + *batch
		if end > len(in.Records) {
			end = len(in.Records)
		}
		chunk := in
		chunk.Records = in.Records[start:end]
		res, err := store.Ingest(ctx, chunk)
		if err != nil {
			fatal("入庫失敗: %v", err)
		}
		total += res.Total
		inserted += res.Inserted
		updated += res.Updated
	}

	out := map[string]any{
		"ok":       true,
		"db":       *dbPath,
		"type":     in.TypeID,
		"dataset":  in.Dataset,
		"source":   in.Source,
		"total":    total,
		"inserted": inserted,
		"updated":  updated,
		"dup":      updated,
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	_ = enc.Encode(out)
}

func importFromSQLite(ctx context.Context, dbPath, sqlText, mapFile, titleCol string) ([]records.IncomingRec, error) {
	mapping := map[string]string{}
	if strings.TrimSpace(mapFile) != "" {
		raw, err := os.ReadFile(mapFile)
		if err != nil {
			return nil, err
		}
		if err := json.Unmarshal(raw, &mapping); err != nil {
			return nil, fmt.Errorf("解析 map 失敗: %w", err)
		}
	}
	src, err := sql.Open("sqlite3", "file:"+dbPath+"?mode=ro&_busy_timeout=8000")
	if err != nil {
		return nil, err
	}
	defer src.Close()
	rows, err := src.QueryContext(ctx, sqlText)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	cols, err := rows.Columns()
	if err != nil {
		return nil, err
	}
	out := []records.IncomingRec{}
	for rows.Next() {
		vals := make([]any, len(cols))
		ptrs := make([]any, len(cols))
		for i := range vals {
			ptrs[i] = &vals[i]
		}
		if err := rows.Scan(ptrs...); err != nil {
			return nil, err
		}
		byCol := map[string]string{}
		for i, name := range cols {
			byCol[name] = stringify(vals[i])
		}
		fields := map[string]string{}
		for field, srcCol := range mapping {
			if v, ok := byCol[srcCol]; ok {
				fields[field] = v
			}
		}
		if len(fields) == 0 {
			// 沒給對應就原樣帶過所有欄位。
			for k, v := range byCol {
				fields[k] = v
			}
		}
		title := ""
		if titleCol != "" {
			title = byCol[titleCol]
		}
		out = append(out, records.IncomingRec{
			Title:    title,
			Fields:   fields,
			Evidence: map[string]any{"source_db": dbPath},
		})
	}
	return out, rows.Err()
}

func stringify(v any) string {
	switch t := v.(type) {
	case nil:
		return ""
	case string:
		return strings.TrimSpace(t)
	case []byte:
		return strings.TrimSpace(string(t))
	case int64:
		return strconv.FormatInt(t, 10)
	case float64:
		return strconv.FormatFloat(t, 'f', -1, 64)
	case bool:
		return strconv.FormatBool(t)
	default:
		return fmt.Sprintf("%v", t)
	}
}

func fatal(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "[abort] "+format+"\n", args...)
	os.Exit(2)
}
