package redirect

import (
	"context"
	"errors"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"

	"jysecai/internal/forbidden"
)

// 批次驗證：一次對多個目標做「受控跳轉」驗證。
//
// 單筆複測見 ProbeWithMethod；批次版把同一套邏輯套用到多個目標上，並加上：
//   - 併發上限（避免一次把對方打爆，也避免自己被打爆）
//   - 目標去重
//   - ctx 可取消（長時間批次必須能中途叫停）

const (
	// DefaultBatchConcurrency 是批次驗證預設同時探測的目標數。
	DefaultBatchConcurrency = 4

	// MaxBatchConcurrency 是批次驗證同時探測的目標數上限。
	MaxBatchConcurrency = 32
)

// BatchOptions 是批次驗證的參數。
type BatchOptions struct {
	// Endpoints 是受控端點（跳轉目標）清單；至少要有一個。
	Endpoints []string
	// Param 指定跳轉參數名；留空則依 DetectRedirectParams 逐一嘗試。
	Param string
	// Method 是請求方式，預設 GET。
	Method string
	// Concurrency 是同時探測的目標數；<=0 時用 DefaultBatchConcurrency。
	Concurrency int
	// Timeout 是單次探測逾時；<=0 時沿用 client 的設定。
	Timeout time.Duration
	// Encoding 是受控端點寫進 payload 時的編碼方式（見 encode.go）。
	//
	// 語意是「目標自己解碼之後應該看到的值」：
	//   - none：原樣（一般情況；URL 建構器會做一次標準 percent-encoding）。
	//   - percent：目標解碼後看到 https%3A%2F%2F… —— 給「會解兩層」或
	//     「過濾器只解一層」的站點用。
	//
	// 編碼不改變它指向哪裡；驗證時會把編碼形式解回來比對，所以
	// 「編碼植入 → 目標解碼跳轉」仍然算命中。
	Encoding string
	// Repeat 是同一個目標要重複探測幾次（預設 1 = 不重複）。
	//
	// 為什麼要這個：命中一次可能是巧合（站方剛好在那個時間回應、負載平衡
	// 打到不同後端）。重複複測可以量出「穩不穩」—— 每次結果一致才算可信。
	// 注意：每次都會真的送出請求，所以對第三方站點是額外噪音，
	// 預設關掉，需要時才開。
	Repeat int
}

// BatchTargetResult 是單一目標的驗證結果。
type BatchTargetResult struct {
	URL        string `json:"url"`
	Confirmed  bool   `json:"confirmed"`
	Param      string `json:"param"`
	RequestURL string `json:"request_url"`
	Status     int    `json:"status"`
	Location   string `json:"location"`
	Error      string `json:"error,omitempty"`
	// OwnParam 是目標網址本來就帶著的跳轉參數名（空字串代表沒有）。
	//
	// 這是「站點本來跳轉的方法」：有值代表站上真的有這條跳轉路徑，
	// 沒值代表這筆是用猜的參數名盲試的 —— 兩者的成敗意義完全不同。
	OwnParam string `json:"own_param,omitempty"`
	// ParamsTried 是實際送出過的參數名清單（依送出順序）。
	//
	// 沒有這個欄位時，報表只會顯示「最後一次試的參數」（常是 u），
	// 讓人誤以為只試過一個參數 —— 實際上未指定參數時會逐一試過整組清單。
	ParamsTried []string `json:"params_tried,omitempty"`
	// Evidence 是證據等級（見 Evidence* 常數）。
	//
	//   - location：3xx 且 Location 指向受控端點 → 真跳轉（強證據）。
	//   - body_echo：本文裡出現受控端點但沒有 Location → 站方只是回顯，
	//     不是跳轉；這類**不計入 confirmed**，是精準度報告裡的偽陽性來源。
	//   - none：沒有任何證據。
	Evidence string `json:"evidence,omitempty"`
	// BodyEcho 為 true 表示是回應本文回顯（疑似偽陽性）。
	BodyEcho bool `json:"body_echo,omitempty"`
	// OwnParamHit 為 true 表示命中的參數就是「站上本來就有的那個」，
	// 而不是我們猜的參數名。站上真的有這條跳轉路徑時才會是 true ——
	// 這是「準不準」最直接的指標。
	OwnParamHit bool `json:"own_param_hit,omitempty"`
	// Attempts 是這個目標實際送出的探測次數（BatchOptions.Repeat > 1 時 > 1）。
	Attempts int `json:"attempts,omitempty"`
	// Stable 為 true 表示重複探測的結果完全一致（沒有 flaky）。
	// Attempts <= 1 時為 true（沒有重複可比）。
	Stable bool `json:"stable"`
}

// VerifyTargets 對一組目標做批次受控跳轉驗證。
//
// 回傳結果與輸入目標一一對應（同序、同長度），方便前端直接對照顯示。
// 沒有可用的受控端點時回傳錯誤；個別目標失敗只會寫在該筆結果的 Error 欄位，
// 不會中斷整批。
func VerifyTargets(ctx context.Context, client *http.Client, targets []string, opts BatchOptions) ([]BatchTargetResult, error) {
	endpoints := NormalizeURLs(opts.Endpoints)
	if len(endpoints) == 0 {
		return nil, errors.New("没有可用的受控端点")
	}
	if ctx == nil {
		ctx = context.Background()
	}
	clean := dedupeTargets(targets)
	results := make([]BatchTargetResult, len(clean))
	if len(clean) == 0 {
		return results, nil
	}

	probeClient := client
	if probeClient == nil {
		probeClient = &http.Client{Timeout: DefaultProbeTimeout}
	}
	if opts.Timeout > 0 {
		copied := *probeClient
		copied.Timeout = opts.Timeout
		probeClient = &copied
	}

	concurrency := opts.Concurrency
	if concurrency <= 0 {
		concurrency = DefaultBatchConcurrency
	}
	if concurrency > MaxBatchConcurrency {
		concurrency = MaxBatchConcurrency
	}
	if concurrency > len(clean) {
		concurrency = len(clean)
	}

	jobs := make(chan int)
	var wg sync.WaitGroup
	for w := 0; w < concurrency; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for idx := range jobs {
				results[idx] = verifyTarget(ctx, probeClient, clean[idx], endpoints, opts)
			}
		}()
	}
	for idx := range clean {
		if ctx.Err() != nil {
			results[idx] = BatchTargetResult{URL: clean[idx], Error: "已取消"}
			continue
		}
		jobs <- idx
	}
	close(jobs)
	wg.Wait()
	return results, nil
}

// verifyTarget 驗證單一目標。
//
// 指定參數名時只探一次；未指定時依常見跳轉參數逐一嘗試，任一次命中就結束該目標的探測。
func verifyTarget(ctx context.Context, client *http.Client, target string, endpoints []string, opts BatchOptions) BatchTargetResult {
	result := BatchTargetResult{URL: target}
	if err := ctx.Err(); err != nil {
		result.Error = "已取消"
		return result
	}
	if err := validateTargetURL(target); err != nil {
		result.Error = err.Error()
		return result
	}
	// 119／EPCR／消防救護類永久禁區：這裡是實際發出 HTTP 請求前的最後一道閘。
	// 批次驗證的目標常是從漏洞庫匯入的，而漏洞庫裡確實有禁區資產的紀錄。
	if reason := forbidden.Reason("", target, "", target, ""); reason != "" {
		result.Error = "目标属于 119／EPCR／消防救护永久禁区，已跳过（" + reason + "）"
		return result
	}

	param := strings.TrimSpace(opts.Param)
	// 目標自己帶著的跳轉參數：站上真的有這條路徑，值得記錄下來。
	if own := OwnRedirectParams(target); len(own) > 0 {
		result.OwnParam = own[0]
	}
	if param != "" {
		result.ParamsTried = []string{param}
	} else {
		result.ParamsTried = DetectRedirectParams(target)
	}
	// 受控端點寫進 payload 的形式：可以選擇編碼（見 encode.go）。
	encoding, err := NormalizePayloadEncoding(opts.Encoding)
	if err != nil {
		result.Error = err.Error()
		return result
	}
	repeat := opts.Repeat
	if repeat <= 0 {
		repeat = 1
	}

	for _, endpoint := range endpoints {
		payload, encodeErr := EncodeEndpoint(endpoint, encoding)
		if encodeErr != nil {
			result.Error = encodeErr.Error()
			return result
		}
		for _, candidate := range result.ParamsTried {
			hits := 0
			attempts := 0
			var last ProbeResult
			for i := 0; i < repeat; i++ {
				if ctx.Err() != nil {
					result.Error = "已取消"
					return result
				}
				probe := ProbeWithMethod(ctx, client, opts.Method, target, candidate, payload)
				attempts++
				result.Attempts += 1
				last = probe
				if probe.Reflected {
					hits++
				}
			}
			// 穩定度：同一組參數重複探測的結果是否一致。
			// 沒有命中也算一致（一致地沒跳轉也是一種確定）。
			result.Stable = hits == 0 || hits == attempts
			applyProbe(&result, last)
			if hits > 0 {
				result.Confirmed = true
				// 命中的參數就是站上本來就有的那一個嗎？
				// 是 → 命中的是站上真的跳轉路徑；不是 → 是我們猜的參數名。
				result.OwnParamHit = result.OwnParam != "" && result.OwnParam == candidate
				return result
			}
		}
	}
	return result
}

// applyProbe 把單次探測結果寫進批次結果。
//
// 後來的探測覆蓋先前的：命中時最後一次探測就是證據本身，失敗時最後一次也最能代表
// 目標目前的狀態（連不上就是連不上）。
func applyProbe(result *BatchTargetResult, probe ProbeResult) {
	result.Confirmed = probe.Reflected
	result.Param = probe.Param
	result.RequestURL = probe.RequestURL
	result.Status = probe.Status
	result.Location = probe.Location
	result.Error = probe.Error
	result.Evidence = probe.Evidence
	result.BodyEcho = probe.BodyEcho
}

// dedupeTargets 去除空白與重複目標，保留輸入順序。
func dedupeTargets(targets []string) []string {
	out := make([]string, 0, len(targets))
	seen := make(map[string]struct{}, len(targets))
	for _, raw := range targets {
		value := strings.TrimSpace(raw)
		if value == "" {
			continue
		}
		if _, exists := seen[value]; exists {
			continue
		}
		seen[value] = struct{}{}
		out = append(out, value)
	}
	return out
}

// validateTargetURL 檢查目標是否為可探測的 http/https 網址。
func validateTargetURL(target string) error {
	parsed, err := url.Parse(strings.TrimSpace(target))
	if err != nil {
		return err
	}
	if parsed.Scheme != "http" && parsed.Scheme != "https" {
		return errors.New("目标 URL 仅支持 http/https")
	}
	if parsed.Host == "" {
		return errors.New("目标 URL 缺少主机名")
	}
	return nil
}
