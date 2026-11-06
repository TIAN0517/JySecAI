package app

import (
	"fmt"
	"strings"

	"jysecai/internal/database"
)

// recordChainFact 把攻擊鏈寫成黑板事實，並用關係邊把各環節連到鏈上。
//
// 為什麼鏈要另外寫一條事實：漏洞記錄是「可交付的 finding」，事實是「可復現的上下文」。
// 鏈的真正價值在順序與因果 —— 這件事只在事實的 body 與 edges 裡看得到。
//
// 邊的 from 指向「對應到某條漏洞的事實」。找不到對應事實時（例如該漏洞是直接落庫、
// 沒有配套事實），就退而求其次用 discovery/ 節點描述該環節，避免邊的 from 指向
// 不存在的 fact_key（那會在黑板圖上變成孤兒節點）。
func recordChainFact(db *database.DB, projectID, conversationID string, chain *database.Vulnerability, steps []ChainStep) {
	if db == nil || chain == nil || strings.TrimSpace(projectID) == "" {
		return
	}

	factKey := "chain/" + chainSlug(chain.Title)
	body := buildChainFactBody(chain, steps)

	confidence := "tentative"
	if chain.Confidence >= database.VulnerabilityConfirmConfidenceThreshold {
		confidence = "confirmed"
	}

	if _, err := db.UpsertProjectFact(&database.ProjectFact{
		ProjectID:              projectID,
		FactKey:                factKey,
		Category:               "chain",
		Summary:                chainFactSummary(chain),
		Body:                   body,
		Confidence:             confidence,
		SourceConversationID:   conversationID,
		RelatedVulnerabilityID: chain.ID,
	}); err != nil {
		return
	}

	edges := make([]database.ProjectFactEdgeFromInput, 0, len(steps))
	for _, step := range steps {
		from := findFactKeyForVulnerability(db, projectID, step.ID)
		if from == "" {
			from = "discovery/" + chainSlug(step.Title)
		}
		edges = append(edges, database.ProjectFactEdgeFromInput{
			From:       from,
			Type:       "part_of",
			Confidence: confidence,
		})
	}
	if len(edges) > 0 {
		_ = db.ReplaceIncomingProjectFactEdges(projectID, factKey, edges)
	}
}

// chainFactSummary 黑板索引用的一行摘要：什麼 + 在哪 + 如何驗證。
func chainFactSummary(chain *database.Vulnerability) string {
	summary := fmt.Sprintf("攻擊鏈 %s（%s）：%s", chain.ID, chain.Severity, chain.Title)
	if strings.TrimSpace(chain.Target) != "" {
		summary += "｜目標 " + chain.Target
	}
	summary += fmt.Sprintf("｜以 %d/100 證據可信度驗證", chain.Confidence)
	return summary
}

// buildChainFactBody 事實 body：完整可復現上下文。
func buildChainFactBody(chain *database.Vulnerability, steps []ChainStep) string {
	var b strings.Builder
	b.WriteString("## 結論\n")
	b.WriteString(chain.Description)
	b.WriteString("\n\n## 目標與入口\n")
	b.WriteString(strings.TrimSpace(chain.Target))
	b.WriteString("\n\n## 攻擊鏈\n")
	for i, step := range steps {
		fmt.Fprintf(&b, "%d. [%s] %s\n", i+1, step.ID, step.Title)
	}
	b.WriteString("\n## Exploit/POC\n")
	b.WriteString(chain.ReproSteps)
	b.WriteString("\n\n## 關鍵證據\n")
	b.WriteString(chain.Evidence)
	b.WriteString("\n\n## 關聯\n")
	b.WriteString("related_vulnerability_id: " + chain.ID)
	return b.String()
}

// findFactKeyForVulnerability 找出與某條漏洞關聯的事實 fact_key。
// 找不到回空字串（呼叫端會退用 discovery/ 節點）。
func findFactKeyForVulnerability(db *database.DB, projectID, vulnerabilityID string) string {
	if db == nil || strings.TrimSpace(projectID) == "" || strings.TrimSpace(vulnerabilityID) == "" {
		return ""
	}
	facts, err := db.ListProjectFacts(projectID, database.ProjectFactListFilter{
		RelatedVulnerabilityID: vulnerabilityID,
	}, 5, 0)
	if err != nil {
		return ""
	}
	for _, fact := range facts {
		if fact == nil || strings.TrimSpace(fact.FactKey) == "" {
			continue
		}
		if strings.EqualFold(fact.Confidence, "deprecated") {
			continue
		}
		return fact.FactKey
	}
	return ""
}

// chainSlug 產生事實 key 用的 slug：小寫、只留英數與連字號。
func chainSlug(title string) string {
	var b strings.Builder
	prevDash := false
	for _, r := range strings.ToLower(strings.TrimSpace(title)) {
		switch {
		case (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9'):
			b.WriteRune(r)
			prevDash = false
		default:
			if !prevDash && b.Len() > 0 {
				b.WriteRune('-')
				prevDash = true
			}
		}
	}
	slug := strings.Trim(b.String(), "-")
	if len(slug) > 80 {
		slug = slug[:80]
	}
	if slug == "" {
		return "escalated-chain"
	}
	return slug
}
