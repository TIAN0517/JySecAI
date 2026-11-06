// Command redirectprobe 是「批次受控跳轉驗證」的命令列版本。
//
// 為什麼需要它
// ------------
// 網頁控制台（批次跳轉驗證頁）適合日常操作，但有兩種情況網頁不方便：
//   - 目標清單來自腳本（既有漏洞匯出、情蒐結果），要一次灌幾百筆
//   - 環境沒有瀏覽器，或只想快速確認某一批目標還能不能重現
//
// 這支 CLI 走的是與網頁完全相同的程式路徑（internal/redirect.VerifyTargets），
// 所以 119／EPCR／消防救護永久禁區守門、參數偵測、代理出口都一樣。
//
// 用法
// ----
//	# 目標清單每行一個 URL（# 開頭為註解）；URL 後面接 TAB 再接參數名可指定跳轉參數
//	redirectprobe -targets targets.txt -endpoint https://your.callback/x
//
//	# 參數名留空就自動偵測（目標既有 query 優先，再試常見跳轉參數名）
//	redirectprobe -targets vulns.txt -endpoint https://your.callback/x
//
//	# 只看會注入什麼、不發任何請求
//	redirectprobe -targets vulns.txt -endpoint https://your.callback/x -dry-run
//
//	# 輸出 JSON 供後續處理
//	redirectprobe -targets vulns.txt -endpoint https://your.callback/x -json
package main

import (
	"bufio"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"jysecai/internal/forbidden"
	"jysecai/internal/redirect"
)

// targetSpec 是目標清單的一行。
//
// Param 是選填的跳轉參數名；留空代表讓引擎自動偵測。
type targetSpec struct {
	URL   string `json:"url"`
	Param string `json:"param,omitempty"`
}

func main() {
	var (
		targetsFile = flag.String("targets", "", "目標清單檔（每行一個 URL，可選「URL<TAB>參數名」；'#' 為註解）；'-' 代表標準輸入")
		endpoint    = flag.String("endpoint", "", "受控端點（要植入的跳轉目標 URL）；可逗號分隔多個")
		param       = flag.String("param", "", "全域跳轉參數名；留空則自動偵測")
		method      = flag.String("method", "GET", "請求方式：GET 或 POST")
		timeoutSecs = flag.Int("timeout", 10, "單次探測逾時（秒）")
		proxyURL    = flag.String("proxy", "", "代理出口（http/https/socks5/socks5h/socks4/socks4a）")
		jsonOut     = flag.Bool("json", false, "以 JSON 輸出結果")
		dryRun      = flag.Bool("dry-run", false, "只列出會被探測的目標與注入後的 URL，不發出任何請求")
	)
	flag.Parse()

	endpoints := splitList(*endpoint)
	if len(endpoints) == 0 {
		fail("必須用 -endpoint 指定受控端點（要植入的跳轉目標）")
	}

	specs, err := readTargets(*targetsFile)
	if err != nil {
		fail(err.Error())
	}
	if len(specs) == 0 {
		fail("目標清單是空的")
	}

	// 禁區守門：批次會真的對外發請求，禁區目標必須擋下。
	urls := make([]string, 0, len(specs))
	for _, spec := range specs {
		urls = append(urls, spec.URL)
	}
	allowedURLs, dropped := forbidden.FilterTargets(urls)
	if len(dropped) > 0 {
		fmt.Fprintf(os.Stderr, "[禁區] 跳過 %d 個 119／EPCR／消防救護永久禁區目標：\n", len(dropped))
		for _, item := range dropped {
			fmt.Fprintf(os.Stderr, "  - %s\n", item)
		}
	}
	if len(allowedURLs) == 0 {
		fail("所有目標都屬於 119／EPCR／消防救護永久禁區，已拒絕執行")
	}
	allowed := make(map[string]struct{}, len(allowedURLs))
	for _, url := range allowedURLs {
		allowed[url] = struct{}{}
	}

	globalParam := strings.TrimSpace(*param)
	if *dryRun {
		for _, spec := range specs {
			if _, ok := allowed[spec.URL]; !ok {
				continue
			}
			params := []string{}
			switch {
			case spec.Param != "":
				params = []string{spec.Param}
			case globalParam != "":
				params = []string{globalParam}
			default:
				params = redirect.DetectRedirectParams(spec.URL)
			}
			for _, p := range params {
				for _, endpoint := range endpoints {
					probeURL, buildErr := redirect.BuildProbeURL(spec.URL, p, endpoint)
					if buildErr != nil {
						fmt.Printf("%s\t%s\t-%v\n", spec.URL, p, buildErr)
						continue
					}
					fmt.Printf("%s\t%s\t%s\n", spec.URL, p, probeURL)
				}
			}
		}
		return
	}

	client, err := redirect.NewVerifyClient(strings.TrimSpace(*proxyURL), time.Duration(*timeoutSecs)*time.Second)
	if err != nil {
		fail("代理設置無效: " + err.Error())
	}

	// 逐目標帶自己的參數名：批次引擎每次只試一個參數，所以同一批裡可以混用不同參數。
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(*timeoutSecs)*time.Duration(len(specs)*4+2)*time.Second)
	defer cancel()

	results := make([]redirect.BatchTargetResult, 0, len(specs))
	for _, spec := range specs {
		if _, ok := allowed[spec.URL]; !ok {
			results = append(results, redirect.BatchTargetResult{
				URL:   spec.URL,
				Error: "目标属于 119／EPCR／消防救护永久禁区，已跳过",
			})
			continue
		}
		effective := spec.Param
		if effective == "" {
			effective = globalParam
		}
		batchResults, batchErr := redirect.VerifyTargets(ctx, client, []string{spec.URL}, redirect.BatchOptions{
			Endpoints: endpoints,
			Param:     effective,
			Method:    strings.ToUpper(strings.TrimSpace(*method)),
		})
		if batchErr != nil {
			results = append(results, redirect.BatchTargetResult{URL: spec.URL, Error: batchErr.Error()})
			continue
		}
		results = append(results, batchResults...)
	}

	if *jsonOut {
		encoder := json.NewEncoder(os.Stdout)
		encoder.SetIndent("", "  ")
		if err := encoder.Encode(map[string]any{
			"endpoints":         endpoints,
			"skipped_forbidden": dropped,
			"results":           results,
		}); err != nil {
			fail(err.Error())
		}
		return
	}

	confirmed := 0
	fmt.Printf("%-8s %-16s %-5s %s\n", "結果", "參數", "狀態", "URL")
	for _, result := range results {
		verdict := "未確認"
		if result.Confirmed {
			verdict = "已確認"
			confirmed++
		}
		fmt.Printf("%-8s %-16s %-5d %s\n", verdict, result.Param, result.Status, result.URL)
		if result.Error != "" {
			fmt.Printf("         └─ %s\n", result.Error)
		}
		if result.Location != "" {
			fmt.Printf("         └─ Location: %s\n", result.Location)
		}
		if result.RequestURL != "" {
			fmt.Printf("         └─ 注入後: %s\n", result.RequestURL)
		}
	}
	fmt.Printf("\n合計 %d 筆，已確認 %d 筆，禁區跳過 %d 筆\n", len(results), confirmed, len(dropped))
}

// readTargets 讀取目標清單。支援「URL<TAB>參數名」與「URL<TAB>參數名<TAB>說明」。
func readTargets(path string) ([]targetSpec, error) {
	if strings.TrimSpace(path) == "" {
		return nil, fmt.Errorf("必須用 -targets 指定目標清單（'-' 代表標準輸入）")
	}
	var scanner *bufio.Scanner
	if path == "-" {
		scanner = bufio.NewScanner(os.Stdin)
	} else {
		file, err := os.Open(path)
		if err != nil {
			return nil, fmt.Errorf("讀取目標清單失敗: %w", err)
		}
		defer file.Close()
		scanner = bufio.NewScanner(file)
		scanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	}
	out := make([]targetSpec, 0, 32)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.Split(line, "\t")
		spec := targetSpec{URL: strings.TrimSpace(parts[0])}
		if spec.URL == "" {
			continue
		}
		if len(parts) > 1 {
			spec.Param = strings.TrimSpace(parts[1])
		}
		out = append(out, spec)
	}
	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("讀取目標清單失敗: %w", err)
	}
	return out, nil
}

func splitList(raw string) []string {
	out := make([]string, 0, 2)
	for _, item := range strings.Split(raw, ",") {
		item = strings.TrimSpace(item)
		if item != "" {
			out = append(out, item)
		}
	}
	return out
}

func fail(message string) {
	fmt.Fprintln(os.Stderr, "錯誤: "+message)
	os.Exit(1)
}
