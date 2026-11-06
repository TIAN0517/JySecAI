package scope

import (
	"context"
	"net"
	"strings"
	"time"
)

// 衍生目標（derived target）：可由既有常駐授權推導出來的目標。
//
// 為什麼需要這個概念
// ------------------
// 滲透測試的授權是「一份授權書涵蓋一個範圍」，但攻擊面會長：授權 example.com 之後，
// DNS 會冒出 api.example.com、cdn.example.com，DNS 記錄裡的 10.20.0.7 也在同一個
// 授權網段裡。這些目標每一個都要人工裁決一次「授權卡片」，是操作負擔的來源；
// 但它們確實落在同一份書面授權的範圍語意內。
//
// 判定規則刻意保守（只看常駐集，且要求明確的包含關係）：
//   1. 子網域：目標主機是某筆常駐 host／wildcard 授權主機的子網域
//      （共享至少兩段標籤，例如 api.example.com ← example.com）。
//   2. 網段：目標 IP 位於某筆常駐 cidr 授權之內（10.20.0.7 ← 10.20.0.0/24）。
//
// 不做的推論（避免把授權範圍撐大）：
//   - 不同網域之間的相似字串（example.com 與 evil-example.com 不會命中）。
//   - 從授權券（一次性授權）推導：授權券是「這一次」，不是「這一類」。
//   - 從已過期或已撤銷的授權推導。
//   - 跨到別的註冊網域（example.com 與 example.com.evil.com 不會命中）。

// DerivedTarget 是一個可由常駐授權推導出來的目標，以及它的推導依據。
type DerivedTarget struct {
	// Target 是被推導出來的目標。
	Target Target
	// SourceID 是來源常駐授權（scope_targets.id）。
	SourceID string
	// SourceValue 是來源授權的主機或網段文字。
	SourceValue string
	// SourceOwner 是來源授權的 owner；新推導出來的目標沿用同一個 owner。
	SourceOwner string
	// ActionClasses 是來源授權容許的動作類別；推導出來的目標不放大權限。
	ActionClasses []string
	// ValidFrom / ValidUntil 沿用來源授權的期間；來源到期，推導目標跟著到期。
	ValidFrom  *time.Time
	ValidUntil *time.Time
}

// DerivedTargets 找出可由常駐集推導出來的未覆蓋目標。
//
// uncovered 是 Resolve 回報的未覆蓋目標；at 是判定基準時間（零值代表現在）。
// 回傳結果依 uncovered 的順序排列，同一個來源只會讓一筆目標被推導（最接近的那筆優先）。
func (s *Service) DerivedTargets(ctx context.Context, uncovered []Target, at time.Time) ([]DerivedTarget, error) {
	if s == nil || s.q == nil {
		return nil, nil
	}
	if len(uncovered) == 0 {
		return nil, nil
	}
	if at.IsZero() {
		at = time.Now()
	}
	rows, err := s.loadScopeRows(ctx)
	if err != nil {
		return nil, err
	}
	// 只從仍然有效（未過期）的常駐授權推導。
	active := make([]scopeRow, 0, len(rows))
	for _, row := range rows {
		if reason, _ := scopeRowExpired(row, at); reason != "" {
			continue
		}
		active = append(active, row)
	}

	var out []DerivedTarget
	for _, target := range uncovered {
		row, ok := findDerivationRow(active, target)
		if !ok {
			continue
		}
		out = append(out, DerivedTarget{
			Target:        target,
			SourceID:      row.id,
			SourceValue:   row.value,
			SourceOwner:   row.owner,
			ActionClasses: effectiveClasses(row.classes),
			ValidFrom:     row.validFrom,
			ValidUntil:    row.validUntil,
		})
	}
	return out, nil
}

// findDerivationRow 找出能推導出該目標的常駐授權。
//
// 比對順序與涵蓋關係一致：host／wildcard（子網域）→ cidr（網段包含）。
// 同一個目標可能同時被多筆授權推導，此時取最具體的那筆（共享標籤最多者優先）。
func findDerivationRow(rows []scopeRow, target Target) (scopeRow, bool) {
	var (
		best      scopeRow
		bestScore int
		found     bool
	)
	for _, row := range rows {
		score := 0
		switch row.kind {
		case TargetHost, TargetWildcard:
			score = derivationScoreSubdomain(row, target)
		case TargetCIDR:
			score = derivationScoreCIDR(row, target)
		default:
			score = 0
		}
		if score <= 0 {
			continue
		}
		if !found || score > bestScore {
			best = row
			bestScore = score
			found = true
		}
	}
	return best, found
}

// derivationScoreSubdomain 判斷目標是否為該筆 host／wildcard 授權的子網域。
//
// 判準是「目標主機以 .<授權主機> 結尾」：授權 api.example.com 時，
// new.api.example.com 是它的子網域（可推導），但 notapi.example.com 只是同層的
// 兄弟網域（只共享 example.com 兩段標籤，不可推導）。用共享標籤數判斷會把兄弟
// 網域也拉進來 —— 那會把授權範圍撐到沒有書面依據的地方。
//
// 回傳共享標籤段數作為分數（越大越具體）；不是子網域時回傳 0。
func derivationScoreSubdomain(row scopeRow, target Target) int {
	if target.Host == "" {
		return 0
	}
	rowHost := adjacentComparableHost(scopeHost(row.value))
	targetHost := adjacentComparableHost(target.Host)
	if rowHost == "" || targetHost == "" || rowHost == targetHost {
		// 同一個主機不算「衍生」——那是涵蓋，不是推導。
		return 0
	}
	if !strings.HasSuffix(targetHost, "."+rowHost) {
		return 0
	}
	labels := strings.Split(rowHost, ".")
	if len(labels) < 2 {
		return 0
	}
	return len(labels)
}

// derivationScoreCIDR 判斷目標 IP 是否位於該筆網段授權之內。
func derivationScoreCIDR(row scopeRow, target Target) int {
	if target.Host == "" {
		return 0
	}
	_, network, err := net.ParseCIDR(strings.TrimSpace(row.value))
	if err != nil {
		return 0
	}
	ip := net.ParseIP(target.Host)
	if ip == nil {
		return 0
	}
	if !network.Contains(ip) {
		return 0
	}
	// 分數用網段遮罩大小：越小（範圍越大）分數越低，但只要命中就是命中。
	ones, _ := network.Mask.Size()
	return 32 - ones + 1
}
