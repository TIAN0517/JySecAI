package poc

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	"jysecai/internal/database"
)

const (
	DraftDirName      = "poc_drafts"
	MarkerTraditional = "> [自動生成 POC/EXP 草稿]"
	MarkerSimplified  = "> [自动生成 POC/EXP 草稿]"
	DefaultMarker     = MarkerSimplified
)

// HasPocDraftMarker 檢查 evidence 是否已包含草稿標記（兼容簡體與繁體）
func HasPocDraftMarker(evidence string) bool {
	return strings.Contains(evidence, MarkerTraditional) || strings.Contains(evidence, MarkerSimplified)
}

var filenameCleanRe = regexp.MustCompile(`[^\p{L}\p{N}\-_]+`)

// GenerateResult 是生成 POC 草稿的結果結構
type GenerateResult struct {
	VulnerabilityID string `json:"vulnerability_id"`
	Title           string `json:"title"`
	Severity        string `json:"severity"`
	Target          string `json:"target"`
	Filename        string `json:"filename"`
	RelativePath    string `json:"relative_path"`
	FullPath        string `json:"full_path"`
	Markdown        string `json:"markdown"`
	UpdatedEvidence bool   `json:"updated_evidence"`
}

// GeneratePocDraft 生成單個漏洞的 POC/EXP 草稿並保存為 Markdown 文件
func GeneratePocDraft(db *database.DB, vuln *database.Vulnerability, outputDir string, writeEvidence bool) (*GenerateResult, error) {
	if vuln == nil {
		return nil, fmt.Errorf("vulnerability is nil")
	}

	if outputDir == "" {
		outputDir = filepath.Join("data", DraftDirName)
	}
	if err := os.MkdirAll(outputDir, 0o755); err != nil {
		return nil, fmt.Errorf("failed to create poc draft dir: %w", err)
	}

	facts := PocContextFacts(db, vuln, vuln.ProjectID)
	markdown := BuildPocDraftMarkdown(vuln, facts)

	filename := PocFilenameFor(vuln)
	targetPath := filepath.Join(outputDir, filename)
	if err := os.WriteFile(targetPath, []byte(markdown), 0o644); err != nil {
		return nil, fmt.Errorf("failed to write poc draft file: %w", err)
	}

	relPath := filepath.ToSlash(filepath.Join(DraftDirName, filename))
	updated := false
	if writeEvidence && db != nil {
		if err := AppendPocDraftMarker(db, vuln, relPath); err == nil {
			updated = true
		}
	}

	return &GenerateResult{
		VulnerabilityID: vuln.ID,
		Title:           vuln.Title,
		Severity:        vuln.Severity,
		Target:          vuln.Target,
		Filename:        filename,
		RelativePath:    relPath,
		FullPath:        targetPath,
		Markdown:        markdown,
		UpdatedEvidence: updated,
	}, nil
}

// PocFilenameFor 為漏洞生成安全的文件名
func PocFilenameFor(v *database.Vulnerability) string {
	raw := strings.ToLower(strings.TrimSpace(v.Title))
	slug := filenameCleanRe.ReplaceAllString(raw, "-")
	slug = strings.Trim(slug, "-")
	if slug == "" {
		slug = "vuln"
	}
	if len(slug) > 60 {
		slug = slug[:60]
		slug = strings.TrimRight(slug, "-")
	}
	return fmt.Sprintf("%s-%s.md", v.ID, slug)
}

// PocContextFacts 收集與漏洞相關的項目事實（攻擊鏈/利用/POC 上下文）
func PocContextFacts(db *database.DB, vuln *database.Vulnerability, projectID string) []*database.ProjectFact {
	if db == nil || strings.TrimSpace(projectID) == "" {
		return nil
	}
	facts, err := db.ListProjectFactsForIndex(projectID, false)
	if err != nil {
		return nil
	}
	related := make([]*database.ProjectFact, 0)
	for _, f := range facts {
		cat := strings.ToLower(strings.TrimSpace(f.Category))
		if cat != "finding" && cat != "chain" && cat != "exploit" && cat != "poc" && cat != "note" {
			continue
		}
		if strings.TrimSpace(f.RelatedVulnerabilityID) != "" && strings.TrimSpace(f.RelatedVulnerabilityID) != vuln.ID {
			continue
		}
		related = append(related, f)
	}
	sort.SliceStable(related, func(i, j int) bool {
		return related[i].FactKey < related[j].FactKey
	})
	if len(related) > 10 {
		related = related[:10]
	}
	return related
}

// BuildPocDraftMarkdown 根據漏洞記錄與相關項目事實生成 POC/EXP 草稿
func BuildPocDraftMarkdown(v *database.Vulnerability, facts []*database.ProjectFact) string {
	var b strings.Builder
	b.WriteString(fmt.Sprintf("# POC/EXP 草稿 - %s\n\n", fmtVulnTitle(v)))
	b.WriteString(fmt.Sprintf("> 自动生成时间: %s  |  状态: **草稿（未验证）**  |  文件: `%s`\n\n", time.Now().Format("2006-01-02 15:04:05"), PocFilenameFor(v)))

	b.WriteString("## 漏洞信息\n\n")
	fmtKV := func(label, value string) {
		if strings.TrimSpace(value) == "" {
			value = "（未记录）"
		}
		b.WriteString(fmt.Sprintf("- **%s**: %s\n", label, strings.ReplaceAll(value, "\n", " ")))
	}
	fmtKV("漏洞ID", v.ID)
	fmtKV("严重程度", v.Severity)
	fmtKV("状态", v.Status)
	fmtKV("类型", v.Type)
	fmtKV("目标", v.Target)
	if !v.CreatedAt.IsZero() {
		b.WriteString(fmt.Sprintf("- **发现时间**: %s\n", v.CreatedAt.Format("2006-01-02 15:04:05")))
	}
	b.WriteString("\n")

	if strings.TrimSpace(v.Description) != "" {
		b.WriteString("## 漏洞描述\n\n")
		b.WriteString(v.Description + "\n\n")
	}

	if strings.TrimSpace(v.Preconditions) != "" {
		b.WriteString("## 前置条件\n\n")
		b.WriteString(v.Preconditions + "\n\n")
	}

	b.WriteString("## POC / EXP 验证指南\n\n")
	if respSteps := strings.TrimSpace(v.ReproSteps); respSteps != "" {
		b.WriteString("### 复现步骤（来自漏洞记录）\n\n")
		b.WriteString(RenderNumberedBlocks(respSteps) + "\n\n")
	} else {
		b.WriteString("### 复现步骤（待补充）\n\n- （漏洞记录未保存复现步骤，请人工补全验证流程）\n\n")
	}

	b.WriteString("### 验证要点与安全基线\n\n")
	verification := []string{
		"确认目标属于合法授权测试范围，非授权测试属于违法行为",
		"交叉校验目标版本、已知 CVE/公开情报库（可联动 cve-poc-emerging-intel / vuln-intel）",
		"使用最小化无害 payload / HTTP 请求逐步探测，记录原始请求与响应报文",
		"验证失败时记录负结果，避免误报；未经真实环境验证不得标记为 confirmed",
	}
	for _, line := range verification {
		b.WriteString(fmt.Sprintf("- [ ] %s\n", line))
	}
	b.WriteString("\n")

	if strings.TrimSpace(v.Evidence) != "" {
		b.WriteString("### 既有证据 / 原始报文\n\n")
		b.WriteString("```http\n" + strings.TrimRight(v.Evidence, "\n") + "\n```\n\n")
	}

	if len(facts) > 0 {
		b.WriteString("## 相关项目事实（攻击链上下文）\n\n")
		for _, f := range facts {
			b.WriteString(fmt.Sprintf("### %s (%s)\n\n", f.FactKey, f.Confidence))
			if strings.TrimSpace(f.Summary) != "" {
				b.WriteString(fmt.Sprintf("> %s\n\n", f.Summary))
			}
			if strings.TrimSpace(f.Body) != "" {
				b.WriteString(f.Body + "\n\n")
			}
		}
	}

	if strings.TrimSpace(v.Impact) != "" {
		b.WriteString("## 安全影响\n\n")
		b.WriteString(v.Impact + "\n\n")
	}
	if strings.TrimSpace(v.Recommendation) != "" {
		b.WriteString("## 修复建议\n\n")
		b.WriteString(v.Recommendation + "\n\n")
	}
	if strings.TrimSpace(v.RetestNotes) != "" {
		b.WriteString("## 复测验证方法\n\n")
		b.WriteString(v.RetestNotes + "\n\n")
	}

	b.WriteString("## 免责声明\n\n")
	b.WriteString("本文件由 JySecAI 自动生成，仅供安全研究与合法授权渗透测试使用。未经授权对目标进行攻击测试属于违法行为。\n")
	return b.String()
}

// AppendPocDraftMarker 把草稿路徑回寫到漏洞記錄的 evidence 字段（僅追加，不覆蓋，兼容簡繁）
func AppendPocDraftMarker(db *database.DB, vuln *database.Vulnerability, relPath string) error {
	if db == nil || vuln == nil {
		return nil
	}
	marker := fmt.Sprintf("%s %s", DefaultMarker, relPath)
	if HasPocDraftMarker(vuln.Evidence) || strings.Contains(vuln.Evidence, relPath) {
		return nil
	}
	newEvidence := strings.TrimRight(vuln.Evidence, "\n")
	if newEvidence != "" {
		newEvidence += "\n\n"
	}
	newEvidence += marker
	updated := *vuln
	updated.Evidence = newEvidence
	return db.UpdateVulnerability(vuln.ID, &updated)
}

func fmtVulnTitle(v *database.Vulnerability) string {
	if strings.TrimSpace(v.Title) != "" {
		return strings.TrimSpace(v.Title)
	}
	return fmt.Sprintf("漏洞 %s", v.ID)
}

// RenderNumberedBlocks 把記錄中的步驟按行渲染為編號清單
func RenderNumberedBlocks(text string) string {
	lines := strings.Split(strings.TrimSpace(text), "\n")
	var staged []string
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		staged = append(staged, strings.TrimPrefix(strings.TrimPrefix(line, "- "), "1. "))
	}
	var b strings.Builder
	for i, line := range staged {
		b.WriteString(fmt.Sprintf("%d. %s\n", i+1, line))
	}
	return b.String()
}
