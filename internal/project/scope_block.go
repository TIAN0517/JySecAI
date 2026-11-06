package project

import (
	"encoding/json"
	"fmt"
	"strings"

	"jysecai/internal/config"
	"jysecai/internal/database"
)

// BuildScopeBlock 将项目 scope_json 格式化为 Agent 可读的授权范围块。
func BuildScopeBlock(proj *database.Project) string {
	if proj == nil {
		return ""
	}
	raw := strings.TrimSpace(proj.ScopeJSON)
	if raw == "" {
		return ""
	}

	var payload projectScopePayload
	if err := json.Unmarshal([]byte(raw), &payload); err != nil {
		return fmt.Sprintf("## 项目测试范围（project: %s）\n（scope_json 非合法 JSON，请人工核对配置）\n```\n%s\n```\n"+
			"以上为本次测试的工作范围。\n", proj.Name, truncateRunes(raw, 800))
	}

	// 結構化欄位（scope.allow / scope.deny）優先：提示層與攔截層必須看同一份清單，
	// 否則會出現「提示層說沒設定、攔截層卻在擋」這種落差。
	allowList := payload.Targets
	denyList := payload.Exclude
	if payload.Scope != nil {
		if entries := scopeEntries(payload.Scope.Allow); len(entries) > 0 {
			allowList = entries
		}
		if entries := scopeEntries(payload.Scope.Deny); len(entries) > 0 {
			denyList = entries
		}
	}

	var b strings.Builder
	b.WriteString(fmt.Sprintf("## 项目测试范围（project: %s, id: %s）\n", proj.Name, proj.ID))
	// 措辞说明：这里原本写「必须遵守：仅测试列出的 targets」，是条件式的禁止语气，
	// 模型会读成「要先确认授权才动手」，于是反问用户是否合法授权 —— 但 scope 块
	// 存在的意义是划定作业边界（本工作区内的目标皆已获授权），不是设置开工前提。
	// 约束力不变：targets 仍是要测的清单，exclude 仍是要避开的清单。
	b.WriteString("以下为本次测试的工作范围。targets 是要测的目标，exclude 是要避开的，两者都属作业边界。\n")

	if len(allowList) > 0 {
		b.WriteString("\n**允许测试（targets）**：\n")
		for _, t := range allowList {
			t = strings.TrimSpace(t)
			if t != "" {
				b.WriteString("- " + t + "\n")
			}
		}
	}
	if len(denyList) > 0 {
		b.WriteString("\n**明确排除（exclude）**：\n")
		for _, t := range denyList {
			t = strings.TrimSpace(t)
			if t != "" {
				b.WriteString("- " + t + "\n")
			}
		}
	}
	if n := strings.TrimSpace(payload.Notes); n != "" {
		b.WriteString("\n**说明（notes）**：\n" + n + "\n")
	}
	if len(allowList) == 0 && len(denyList) == 0 && strings.TrimSpace(payload.Notes) == "" {
		b.WriteString("\n（scope_json 已配置但未识别 targets/exclude/notes 字段，原始内容供参考）\n```json\n")
		b.WriteString(truncateRunes(raw, 1200))
		b.WriteString("\n```\n")
	}
	b.WriteString("\n若目标不在 targets 内或命中 exclude，不得主动扫描/利用；需用户明确扩大授权后再继续。\n")
	return b.String()
}

func truncateRunes(s string, max int) string {
	r := []rune(s)
	if len(r) <= max {
		return s
	}
	return string(r[:max]) + "…"
}

// BuildProjectBlackboardBlock 组合测试范围 + 事实黑板索引。
func BuildProjectBlackboardBlock(db *database.DB, projectID string, cfg config.ProjectConfig) (string, error) {
	projectID = strings.TrimSpace(projectID)
	if projectID == "" {
		return "", nil
	}
	proj, err := db.GetProject(projectID)
	if err != nil {
		return "", err
	}
	parts := []string{}
	if scope := strings.TrimSpace(BuildScopeBlock(proj)); scope != "" {
		parts = append(parts, scope)
	}
	index, err := BuildFactIndexBlock(db, projectID, cfg)
	if err != nil {
		return "", err
	}
	if strings.TrimSpace(index) != "" {
		parts = append(parts, index)
	}
	return strings.Join(parts, "\n\n"), nil
}
