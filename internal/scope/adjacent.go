package scope

import (
	"context"
	"strings"
	"time"
)

// 相鄰授權（adjacent）與類別授權查詢。
//
// 為什麼需要「相鄰」這個概念
// --------------------------
// 操作者面對一張「這個目標沒被授權」的卡片時，真正需要的資訊不是「沒有授權」，
// 而是「離它最近的授權是什麼、那是誰的」。有了這個線索，操作者按一次批准就能
// 把新目標接在同一個 owner 底下，而不是從零猜一個 owner。
//
// 為什麼不用 public suffix 清單
// ----------------------------
// 相鄰比對刻意只做「純字串後綴比對」：不引入 publicsuffix 依賴、不做 eTLD+1 拆解。
// 理由有兩個：
//  1. 離線環境（GOFLAGS=-mod=mod GOPROXY=off）不能新增模組依賴。
//  2. 授權判斷不該因為「後綴表版本不同」而改變結果——那是稽核敏感的路徑。
// 代價是 *.co.uk 這類多層公共後綴會被當成一般後綴；這在授權語意上是保守的
// （只會讓相鄰判定更嚴格，不會讓授權範圍變大）。

// AdjacentScope 是「與某個未覆蓋目標最接近的既有授權」。
type AdjacentScope struct {
	// Host 是該筆授權涵蓋的主機（wildcard 會去掉 "*." 前綴）。
	Host string
	// Owner 是該筆授權的 owner（新建授權時的 owner 備援來源）。
	Owner string
	// GrantID 是 scope_targets.id。
	GrantID string
	// Source 一律是 scope_target（相鄰只從常駐集取，授權券沒有 owner 概念）。
	Source string
	// ActionClasses 是該筆授權實際容許的動作類別。
	ActionClasses []string
	// ValidUntil 是該筆授權的到期時間（RFC3339）；沒有期限則是空字串。
	ValidUntil string
}

// AdjacentScopes 找出與未覆蓋目標「共享最長後綴」的既有授權。
//
// 比對規則：把兩邊主機名以 "." 拆成標籤，從尾端往回比對相同的標籤；
// 共享標籤至少要有兩段（例如 example.com），或是兩個主機完全相同。
// 完全相同的優先（共享標籤最多），共享標籤數相同時取 target_value 較長者
// （較具體的授權優先）。
//
// 回傳結果依未覆蓋目標的順序排列，同一筆授權只出現一次。
func (s *Service) AdjacentScopes(ctx context.Context, uncovered []Target) ([]AdjacentScope, error) {
	if s == nil || s.q == nil {
		return nil, nil
	}
	if len(uncovered) == 0 {
		return nil, nil
	}
	rows, err := s.loadScopeRows(ctx)
	if err != nil {
		return nil, err
	}
	var out []AdjacentScope
	seen := make(map[string]struct{})
	for _, target := range uncovered {
		best, ok := findAdjacentRow(rows, target)
		if !ok {
			continue
		}
		if _, dup := seen[best.id]; dup {
			continue
		}
		seen[best.id] = struct{}{}
		item := AdjacentScope{
			Host:          adjacentHost(best),
			Owner:         best.owner,
			GrantID:       best.id,
			Source:        SourceScopeTarget,
			ActionClasses: effectiveClasses(best.classes),
		}
		if best.validUntil != nil {
			item.ValidUntil = best.validUntil.UTC().Format(time.RFC3339)
		}
		out = append(out, item)
	}
	return out, nil
}

// findAdjacentRow 找出與目標共享最長後綴的那一筆常駐集授權。
func findAdjacentRow(rows []scopeRow, target Target) (scopeRow, bool) {
	targetHost := adjacentComparableHost(target.Host)
	if targetHost == "" {
		return scopeRow{}, false
	}
	var (
		best      scopeRow
		bestScore int
		bestLen   int
		found     bool
	)
	for _, row := range rows {
		host := adjacentHost(row)
		if host == "" {
			continue
		}
		shared := sharedLabelSuffix(host, targetHost)
		if shared == "" {
			continue
		}
		score := len(shared)
		if host == targetHost {
			// 完全相同：加權，讓它一定贏過只是後綴相同的其他授權。
			score += 1000
		}
		if !found || score > bestScore || (score == bestScore && len(row.value) > bestLen) {
			best = row
			bestScore = score
			bestLen = len(row.value)
			found = true
		}
	}
	return best, found
}

// adjacentHost 取一筆常駐集授權的可比主機名。
func adjacentHost(row scopeRow) string {
	host := scopeHost(row.value)
	if host == "" {
		return ""
	}
	return adjacentComparableHost(host)
}

// adjacentComparableHost 正規化可比主機名：去掉 wildcard 前綴與尾點。
func adjacentComparableHost(host string) string {
	host = strings.ToLower(strings.TrimSpace(host))
	host = strings.TrimPrefix(host, "*.")
	host = strings.TrimSuffix(host, ".")
	return host
}

// sharedLabelSuffix 回傳兩個主機名共享的最長標籤後綴。
//
// 規則：逐標籤自尾端比對；共享後綴必須至少含兩段標籤（example.com），
// 或是兩個主機完全相同（單標籤主機，例如 localhost）。
func sharedLabelSuffix(a, b string) string {
	a = strings.ToLower(strings.TrimSpace(a))
	b = strings.ToLower(strings.TrimSpace(b))
	if a == "" || b == "" {
		return ""
	}
	if a == b {
		return a
	}
	as := strings.Split(a, ".")
	bs := strings.Split(b, ".")
	n := 0
	for n < len(as) && n < len(bs) && as[len(as)-1-n] == bs[len(bs)-1-n] {
		n++
	}
	if n < 2 {
		return ""
	}
	return strings.Join(as[len(as)-n:], ".")
}

// HasActionClassAuthorization 回傳 registry 裡是否有一筆授權「明確列出」該動作類別。
//
// 為什麼要求「明確列出」而不是「空 action_classes 也算」：
// 空 action_classes 的語意是「一般類別全部允許」（harmless_request 等四類），
// 絕不包含 credential_enum／bulk_scan／arbitrary。若放寬成「空也算」，
// 一筆只授權讀取一般資料的常駐集就能讓任意執行類工具通過——那正是 P0 設計
// §3.1 明文禁止的失效方向。
//
// 這個查詢服務於「任意執行類工具」的兜底檢查：這類工具抽不出目標，
// 無法用「目標有沒有被涵蓋」來判定，只能退化成「有沒有針對這個類別的授權」。
// 常駐集與授權券都算（批准「一次」寫的是授權券）。
func (s *Service) HasActionClassAuthorization(ctx context.Context, actionClass string) (bool, error) {
	if s == nil || s.q == nil {
		return false, nil
	}
	actionClass = strings.TrimSpace(actionClass)
	if actionClass == "" {
		actionClass = ActionArbitrary
	}
	rows, err := s.loadScopeRows(ctx)
	if err != nil {
		return false, err
	}
	for _, row := range rows {
		for _, class := range row.classes {
			if strings.EqualFold(strings.TrimSpace(class), actionClass) {
				return true, nil
			}
		}
	}
	grants, err := s.loadGrantRows(ctx)
	if err != nil {
		return false, err
	}
	for _, grant := range grants {
		if strings.EqualFold(strings.TrimSpace(grant.status), "revoked") {
			continue
		}
		for _, class := range grant.classes {
			if strings.EqualFold(strings.TrimSpace(class), actionClass) {
				return true, nil
			}
		}
	}
	return false, nil
}

// IsPermanentBlockedActionClass 判斷動作類別是否屬永久封鎖（destructive／real_transaction）。
//
// 這是 internal/scope 內部比對規則的對外版本：呼叫端需要在「沒有目標」的情況下
// （例如任意執行類工具）也能先擋下永久封鎖的類別。
func IsPermanentBlockedActionClass(actionClass string) bool {
	return isPermanentBlocked(actionClass)
}
