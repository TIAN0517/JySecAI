package scope

import (
	"context"
	"errors"
	"sort"
	"strings"
	"time"
)

// CoverageReport 是授權覆蓋率報告。
//
// 存在的理由：平台手上明明有一堆「已確認的漏洞目標」，但 registry 是空的，
// agent 於是只能退化成拒絕。這份報告把「手上有哪些目標」與「授權了哪些目標」
// 放在同一張表上比對，讓「為什麼一直拒絕」變成可量化的數字而不是猜測。
type CoverageReport struct {
	// Total 是評估的目標總數（已去重）。
	Total int `json:"total"`
	// Covered 是已被 scope_targets 或 scope_grants 涵蓋的目標數。
	Covered int `json:"covered"`
	// Uncovered 是沒有任何授權涵蓋、也沒被拒絕的目標數。
	Uncovered int `json:"uncovered"`
	// Denied 是命中禁區／永久封鎖類別／拒絕記憶的目標數。
	Denied int `json:"denied"`
	// BySource 是涵蓋來源統計（scope_target／scope_grant）。
	BySource map[string]int `json:"by_source"`
	// UncoveredTargets 是未涵蓋目標（已正規化）。
	UncoveredTargets []Target `json:"uncovered_targets"`
	// DeniedTargets 是被拒絕的目標與原因。
	DeniedTargets []Denial `json:"denied_targets"`
	// MatchedGrants 是命中授權券的 ID（供稽核追蹤用）。
	MatchedGrants []string `json:"matched_grants"`
}

// AuditCoverage 評估一組目標在指定動作類別下的授權覆蓋率。
//
// 這是唯讀的：不寫任何資料表，只呼叫既有的 Resolve()，所以報告與平台實際
// 執行的判定語意是同一套——不會出現「報告說覆蓋、實際卻被擋」的落差。
//
// at 是判定基準時間；零值代表現在（時間可注入是為了測試到期語意）。
func AuditCoverage(ctx context.Context, q Queryer, targets []string, actionClass string, at time.Time) (CoverageReport, error) {
	report := CoverageReport{BySource: map[string]int{}}
	if q == nil {
		return report, errors.New("scope 服務尚未初始化（缺少資料庫連線）")
	}
	service := NewService(q)
	result, err := service.Resolve(ctx, dedupeRawTargets(targets), actionClass, at)
	if err != nil {
		return report, err
	}
	report.Covered = len(result.Covered)
	report.Uncovered = len(result.Uncovered)
	report.Denied = len(result.Denied)
	report.Total = report.Covered + report.Uncovered + report.Denied
	for _, match := range result.Covered {
		report.BySource[match.Source]++
		if match.Source == SourceScopeGrant {
			report.MatchedGrants = append(report.MatchedGrants, match.GrantID)
		}
	}
	sort.Strings(report.MatchedGrants)
	report.UncoveredTargets = result.Uncovered
	report.DeniedTargets = result.Denied
	return report, nil
}

// dedupeRawTargets 依正規化後的目標鍵去重，保留第一次出現的原始字串。
//
// 去重是必要的：同一個主機常常同時以 URL、裸主機、IP 的形式出現在不同筆
// 漏洞記錄裡。不去重會讓覆蓋率被同一個目標灌水，看不出真正的缺口。
func dedupeRawTargets(raws []string) []string {
	seen := make(map[string]bool, len(raws))
	out := make([]string, 0, len(raws))
	for _, raw := range raws {
		trimmed := strings.TrimSpace(raw)
		if trimmed == "" {
			continue
		}
		key := NormalizeTarget(trimmed).Key()
		if key == "" || seen[key] {
			continue
		}
		seen[key] = true
		out = append(out, trimmed)
	}
	return out
}
