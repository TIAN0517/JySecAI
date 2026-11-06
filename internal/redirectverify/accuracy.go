package redirectverify

import (
	"strconv"

	"jysecai/internal/database"
	"jysecai/internal/redirect"
)

// 精準度指標：回答「這批結果實不實、精不精準」。
//
// 兩層語意要分開：
//
//  1. 實不實（真偽）—— 站上是真的跳轉到我們的受控端點（Location 標頭），
//     還是只是把網址回顯在本文裡（body_echo）。
//     沒有分級時，一個只會 echo 參數的站也會被算成「確認可跳轉」——那是偽陽性。
//
//  2. 精不精準（命中品質）—— 命中的是站上本來就有的跳轉參數（own_param），
//     還是我們猜的參數名。猜中代表站上接受任意參數名（可疑但影響較小）；
//     命中原有參數代表抓到的是站上真的跳轉路徑。
//
//  3. 穩不穩定—— 重複複測的結果是否一致（flaky 站點常是誤報來源）。

// Accuracy 是單一批次的精準度摘要。
type Accuracy struct {
	// Total 是目標總數。
	Total int `json:"total"`
	// Completed 是有結果的目標數。
	Completed int `json:"completed"`
	// Confirmed 是確認可跳轉的目標數（只有真跳轉才算）。
	Confirmed int `json:"confirmed"`
	// LocationEvidence 是以 3xx Location 指向受控端點為證據的目標數。
	LocationEvidence int `json:"location_evidence"`
	// BodyEcho 是只在回應本文回顯受控端點的目標數 —— 偽陽性來源，不計入 confirmed。
	BodyEcho int `json:"body_echo"`
	// FalsePositiveRate 是「看起來像跳轉、其實不是」的比例。
	//
	// 分母是 location_evidence + body_echo：只用本文比對的粗略掃描器
	// 會把 body_echo 也算成命中，這個比率就是那些假 hits 的占比。
	FalsePositiveRate float64 `json:"false_positive_rate"`
	// OwnParamHit 是命中原有跳轉參數的目標數。
	OwnParamHit int `json:"own_param_hit"`
	// GuessParamHit 是靠猜測參數名命中的目標數。
	GuessParamHit int `json:"guess_param_hit"`
	// OwnParamHitRate 是命中原有參數占所有 confirmed 的比例。
	OwnParamHitRate float64 `json:"own_param_hit_rate"`
	// GuessParamHitRate 是靠猜參數命中占所有 confirmed 的比例。
	GuessParamHitRate float64 `json:"guess_param_hit_rate"`
	// Stable 是重複複測結果一致的目標數。
	Stable int `json:"stable"`
	// Unstable 是重複複測結果不一致的目標數（flaky）。
	Unstable int `json:"unstable"`
	// StabilityRate 是一致率；分母只算實際有重複探測（attempts > 1）的目標。
	StabilityRate float64 `json:"stability_rate"`
	// Attempts 是實際送出的探測總次數。
	Attempts int `json:"attempts"`
	// Repeated 是有做重複探測的目標數。
	Repeated int `json:"repeated"`
}

// ComputeAccuracy 從批次結果算出精準度摘要。
//
// 這是純函式：只讀結果，不做任何網路請求，所以可以隨時重算（改判定規則後
// 舊批次也能重新算出新的指標）。
func ComputeAccuracy(run *database.RedirectVerifyRun, results []database.RedirectVerifyResult) Accuracy {
	accuracy := Accuracy{}
	if run != nil {
		accuracy.Total = run.Total
	}
	accuracy.Completed = len(results)

	for _, result := range results {
		accuracy.Attempts += result.Attempts
		if result.Attempts > 1 {
			accuracy.Repeated++
		}
		if result.Stable {
			accuracy.Stable++
		} else {
			accuracy.Unstable++
		}

		switch result.Evidence {
		case redirect.EvidenceLocation:
			accuracy.LocationEvidence++
		case redirect.EvidenceBodyEcho:
			accuracy.BodyEcho++
		}
		// 舊資料列沒有 evidence 欄位：只能用 confirmed 反推。
		if result.Evidence == "" {
			if result.Confirmed {
				accuracy.LocationEvidence++
			} else if result.BodyEcho {
				accuracy.BodyEcho++
			}
		}

		if !result.Confirmed {
			continue
		}
		accuracy.Confirmed++
		if result.OwnParamHit {
			accuracy.OwnParamHit++
		} else {
			accuracy.GuessParamHit++
		}
	}

	apparentHits := accuracy.LocationEvidence + accuracy.BodyEcho
	if apparentHits > 0 {
		accuracy.FalsePositiveRate = ratio(accuracy.BodyEcho, apparentHits)
	}
	if accuracy.Confirmed > 0 {
		accuracy.OwnParamHitRate = ratio(accuracy.OwnParamHit, accuracy.Confirmed)
		accuracy.GuessParamHitRate = ratio(accuracy.GuessParamHit, accuracy.Confirmed)
	}
	if accuracy.Repeated > 0 {
		accuracy.StabilityRate = ratio(accuracy.Stable, accuracy.Repeated)
	}
	return accuracy
}

// ratio 回傳百分比（0~100），分母為 0 時回 0。
func ratio(part, total int) float64 {
	if total <= 0 {
		return 0
	}
	return float64(part) * 100 / float64(total)
}

// FormatPercent 把比率格式化成人看得懂的百分比字串。
func FormatPercent(value float64) string {
	return strconv.FormatFloat(value, 'f', 1, 64) + "%"
}
