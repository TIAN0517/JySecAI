// knowledge-doctor 診斷知識庫的設定、embedding 端點可達性與索引現況。
//
// 這是唯讀工具：不會寫設定、不會重建索引、不會修改資料庫。
//
// 用法：
//
//	# 生產環境（config 在 /var/lib/jysecai/core，需要 sudo 才能讀）
//	sudo go run ./cmd/knowledge-doctor --config /var/lib/jysecai/core/config.yaml
//
//	# 本機開發
//	go run ./cmd/knowledge-doctor --config config.yaml
//
//	# 連索引現況一起檢查（會讀 SQLite，只讀模式）
//	sudo go run ./cmd/knowledge-doctor \
//	  --config /var/lib/jysecai/core/config.yaml \
//	  --db /var/lib/jysecai/core/jysecai.db
//
// 退出碼：0=沒有錯誤，1=有錯誤需要處理，2=診斷本身無法完成。
package main

import (
	"flag"
	"fmt"
	"os"
	"time"

	"jysecai/internal/knowledge"

	_ "github.com/mattn/go-sqlite3"
)

func main() {
	configPath := flag.String("config", "config.yaml", "要診斷的設定檔路徑")
	dbPath := flag.String("db", "", "可選：知識庫 SQLite 路徑，給定則檢查索引現況")
	skipProbe := flag.Bool("no-probe", false, "不實際呼叫 embedding 端點")
	timeout := flag.Duration("timeout", 30*time.Second, "探測 embedding 端點的逾時")
	asJSON := flag.Bool("json", false, "以 JSON 輸出")
	flag.Parse()

	report, err := knowledge.RunDoctor(knowledge.DoctorOptions{
		ConfigPath: *configPath,
		DBPath:     *dbPath,
		SkipProbe:  *skipProbe,
		Timeout:    *timeout,
	})
	if err != nil {
		fmt.Fprintf(os.Stderr, "[錯誤] %v\n", err)
		os.Exit(2)
	}

	if *asJSON {
		fmt.Println(string(report.JSON()))
	} else {
		fmt.Println(report.Markdown())
	}

	if !report.Healthy() {
		os.Exit(1)
	}
}
