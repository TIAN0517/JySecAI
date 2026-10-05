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
	DefaultMarker     = MarkerTraditional
)

var (
	filenameCleanRe  = regexp.MustCompile(`[^\p{L}\p{N}\-_]+`)
	numberedPrefixRe = regexp.MustCompile(`^\d+[.)]\s*`)
)

// GenerateResult describes a generated, non-executing Markdown draft.
type GenerateResult struct {
	VulnerabilityID string `json:"vulnerability_id"`
	Title           string `json:"title"`
	Severity        string `json:"severity"`
	Target          string `json:"target"`
	Filename        string `json:"filename"`
	RelativePath    string `json:"relative_path"`
	FullPath        string `json:"-"`
	Markdown        string `json:"markdown"`
	UpdatedEvidence bool   `json:"updated_evidence"`
}

// HasPocDraftMarker reports whether evidence already references an auto-generated draft.
func HasPocDraftMarker(evidence string) bool {
	return strings.Contains(evidence, MarkerTraditional) || strings.Contains(evidence, MarkerSimplified)
}

// GeneratePocDraft writes a Markdown draft only. It never sends requests to the target.
func GeneratePocDraft(db *database.DB, vuln *database.Vulnerability, outputDir string, writeEvidence bool) (*GenerateResult, error) {
	if vuln == nil {
		return nil, fmt.Errorf("vulnerability is nil")
	}
	if strings.TrimSpace(vuln.ID) == "" {
		return nil, fmt.Errorf("vulnerability ID is required")
	}
	if strings.TrimSpace(outputDir) == "" {
		outputDir = filepath.Join("data", DraftDirName)
	}
	absOutputDir, err := filepath.Abs(outputDir)
	if err != nil {
		return nil, fmt.Errorf("resolve POC draft directory: %w", err)
	}
	if err := os.MkdirAll(absOutputDir, 0o750); err != nil {
		return nil, fmt.Errorf("create POC draft directory: %w", err)
	}

	facts := PocContextFacts(db, vuln, vuln.ProjectID)
	markdown := BuildPocDraftMarkdown(vuln, facts)
	filename := PocFilenameFor(vuln)
	targetPath := filepath.Join(absOutputDir, filename)
	if err := ensurePathInDir(absOutputDir, targetPath); err != nil {
		return nil, err
	}
	if err := atomicWriteFile(targetPath, []byte(markdown), 0o640); err != nil {
		return nil, fmt.Errorf("write POC draft: %w", err)
	}

	relPath := filepath.ToSlash(filepath.Join(DraftDirName, filename))
	updated := false
	if writeEvidence && db != nil {
		if err := AppendPocDraftMarker(db, vuln, relPath); err != nil {
			return nil, fmt.Errorf("link POC draft to vulnerability: %w", err)
		}
		updated = true
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

func ensurePathInDir(dir, target string) error {
	rel, err := filepath.Rel(dir, target)
	if err != nil {
		return fmt.Errorf("validate POC draft path: %w", err)
	}
	if rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) || filepath.IsAbs(rel) {
		return fmt.Errorf("POC draft path escapes output directory")
	}
	return nil
}

func atomicWriteFile(target string, data []byte, mode os.FileMode) error {
	dir := filepath.Dir(target)
	tmp, err := os.CreateTemp(dir, ".poc-draft-*")
	if err != nil {
		return err
	}
	tmpName := tmp.Name()
	defer os.Remove(tmpName)
	if err := tmp.Chmod(mode); err != nil {
		_ = tmp.Close()
		return err
	}
	if _, err := tmp.Write(data); err != nil {
		_ = tmp.Close()
		return err
	}
	if err := tmp.Sync(); err != nil {
		_ = tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	if err := os.Rename(tmpName, target); err == nil {
		return nil
	}
	// Windows cannot replace an existing file with Rename. The filename is
	// confined above, so a remove-and-rename fallback is safe here.
	if err := os.Remove(target); err != nil && !os.IsNotExist(err) {
		return err
	}
	return os.Rename(tmpName, target)
}

// PocFilenameFor builds a filename entirely from sanitized components.
func PocFilenameFor(v *database.Vulnerability) string {
	id := filenameSlug(v.ID, "vulnerability")
	title := filenameSlug(v.Title, "vuln")
	if len(title) > 60 {
		title = strings.TrimRight(title[:60], "-")
	}
	return fmt.Sprintf("%s-%s.md", id, title)
}

func filenameSlug(raw, fallback string) string {
	slug := filenameCleanRe.ReplaceAllString(strings.ToLower(strings.TrimSpace(raw)), "-")
	slug = strings.Trim(slug, "-")
	if slug == "" {
		return fallback
	}
	return slug
}

// PocContextFacts collects a small, relevant set of project facts for the draft.
func PocContextFacts(db *database.DB, vuln *database.Vulnerability, projectID string) []*database.ProjectFact {
	if db == nil || vuln == nil || strings.TrimSpace(projectID) == "" {
		return nil
	}
	facts, err := db.ListProjectFactsForIndex(projectID, false)
	if err != nil {
		return nil
	}
	related := make([]*database.ProjectFact, 0)
	for _, fact := range facts {
		category := strings.ToLower(strings.TrimSpace(fact.Category))
		switch category {
		case "finding", "chain", "exploit", "poc", "note":
		default:
			continue
		}
		if id := strings.TrimSpace(fact.RelatedVulnerabilityID); id != "" && id != vuln.ID {
			continue
		}
		related = append(related, fact)
	}
	sort.SliceStable(related, func(i, j int) bool { return related[i].FactKey < related[j].FactKey })
	if len(related) > 10 {
		related = related[:10]
	}
	return related
}

// BuildPocDraftMarkdown renders a reviewable draft without executing a payload.
func BuildPocDraftMarkdown(v *database.Vulnerability, facts []*database.ProjectFact) string {
	var b strings.Builder
	b.WriteString(fmt.Sprintf("# POC/EXP 草稿 - %s\n\n", vulnerabilityTitle(v)))
	b.WriteString(fmt.Sprintf("> 自動生成時間: %s  |  狀態: **草稿（未驗證）**  |  檔案: `%s`\n\n", time.Now().Format("2006-01-02 15:04:05"), PocFilenameFor(v)))
	b.WriteString("## 漏洞資訊\n\n")
	writeKV := func(label, value string) {
		value = strings.TrimSpace(strings.ReplaceAll(value, "\n", " "))
		if value == "" {
			value = "（未記錄）"
		}
		b.WriteString(fmt.Sprintf("- **%s**: %s\n", label, value))
	}
	writeKV("漏洞 ID", v.ID)
	writeKV("嚴重程度", v.Severity)
	writeKV("狀態", v.Status)
	writeKV("類型", v.Type)
	writeKV("目標", v.Target)
	if !v.CreatedAt.IsZero() {
		b.WriteString(fmt.Sprintf("- **發現時間**: %s\n", v.CreatedAt.Format("2006-01-02 15:04:05")))
	}
	b.WriteString("\n")
	writeSection(&b, "漏洞描述", v.Description)
	writeSection(&b, "前置條件", v.Preconditions)

	b.WriteString("## POC / EXP 驗證指南\n\n")
	if steps := strings.TrimSpace(v.ReproSteps); steps != "" {
		b.WriteString("### 復現步驟（來自漏洞記錄）\n\n")
		b.WriteString(RenderNumberedBlocks(steps) + "\n")
	} else {
		b.WriteString("### 復現步驟（待補充）\n\n- 漏洞記錄尚未保存復現步驟，請由測試人員補全。\n\n")
	}
	b.WriteString("### 驗證要點與安全基線\n\n")
	for _, line := range []string{
		"確認目標屬於合法授權測試範圍",
		"交叉核對目標版本與公開漏洞情報",
		"使用最小化、無害的請求逐步驗證並保存原始請求與回應",
		"記錄失敗或不確定結果；未經實際驗證不得標記為 confirmed",
	} {
		b.WriteString("- [ ] " + line + "\n")
	}
	b.WriteString("\n")
	if evidence := strings.TrimSpace(v.Evidence); evidence != "" {
		b.WriteString("### 既有證據 / 原始報文\n\n```text\n")
		b.WriteString(strings.TrimRight(evidence, "\n"))
		b.WriteString("\n```\n\n")
	}
	if len(facts) > 0 {
		b.WriteString("## 相關專案事實\n\n")
		for _, fact := range facts {
			b.WriteString(fmt.Sprintf("### %s (%s)\n\n", fact.FactKey, fact.Confidence))
			if summary := strings.TrimSpace(fact.Summary); summary != "" {
				b.WriteString("> " + strings.ReplaceAll(summary, "\n", " ") + "\n\n")
			}
			if body := strings.TrimSpace(fact.Body); body != "" {
				b.WriteString(body + "\n\n")
			}
		}
	}
	writeSection(&b, "安全影響", v.Impact)
	writeSection(&b, "修復建議", v.Recommendation)
	writeSection(&b, "複測驗證方法", v.RetestNotes)
	b.WriteString("## 免責聲明\n\n本文件由 JySecAI 自動生成，只是待人工審核的草稿，僅供合法授權的安全測試使用。\n")
	return b.String()
}

func writeSection(b *strings.Builder, title, body string) {
	if body = strings.TrimSpace(body); body != "" {
		b.WriteString("## " + title + "\n\n" + body + "\n\n")
	}
}

func vulnerabilityTitle(v *database.Vulnerability) string {
	if title := strings.TrimSpace(v.Title); title != "" {
		return title
	}
	return "漏洞 " + v.ID
}

// AppendPocDraftMarker links the file to the vulnerability without replacing evidence.
func AppendPocDraftMarker(db *database.DB, vuln *database.Vulnerability, relPath string) error {
	if db == nil || vuln == nil {
		return nil
	}
	if HasPocDraftMarker(vuln.Evidence) || strings.Contains(vuln.Evidence, relPath) {
		return nil
	}
	evidence := strings.TrimRight(vuln.Evidence, "\n")
	if evidence != "" {
		evidence += "\n\n"
	}
	evidence += fmt.Sprintf("%s %s", DefaultMarker, relPath)
	updated := *vuln
	updated.Evidence = evidence
	if err := db.UpdateVulnerability(vuln.ID, &updated); err != nil {
		return err
	}
	vuln.Evidence = evidence
	return nil
}

// RenderNumberedBlocks normalizes saved reproduction steps into a numbered list.
func RenderNumberedBlocks(text string) string {
	lines := strings.Split(strings.TrimSpace(text), "\n")
	var b strings.Builder
	index := 0
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		line = strings.TrimPrefix(line, "- ")
		line = numberedPrefixRe.ReplaceAllString(line, "")
		index++
		b.WriteString(fmt.Sprintf("%d. %s\n", index, line))
	}
	return b.String()
}
