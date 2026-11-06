package vulnquality

import (
	"fmt"
	"regexp"
	"sort"
	"strings"
)

var reportSecretPatterns = []*regexp.Regexp{
	regexp.MustCompile(`AIza[0-9A-Za-z_-]{20,}`),
	regexp.MustCompile(`(?i)(?:sk|api)[-_][0-9A-Za-z_-]{20,}`),
}

func Markdown(report Report) string {
	var out strings.Builder
	fmt.Fprintf(&out, "# Vulnerability data-quality report\n\nGenerated: %s\n\n", report.GeneratedAt.Format("2006-01-02T15:04:05Z07:00"))
	fmt.Fprintf(&out, "- Total rows: %d\n", report.Total)
	fmt.Fprintf(&out, "- Empty target: %d (%s)\n", report.EmptyTargets.Count, joinIDs(report.EmptyTargets.IDs))
	fmt.Fprintf(&out, "- Filter options after proposed cleanup: %d (must remain non-zero)\n\n", report.FilterOptionsAfterCount)

	out.WriteString("## Dirty vulnerability types\n\n")
	names := make([]string, 0, len(report.DirtyTypes))
	for name := range report.DirtyTypes {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		issue := report.DirtyTypes[name]
		fmt.Fprintf(&out, "- `%s`: %d (%s)\n", name, issue.Count, joinIDs(issue.IDs))
	}

	out.WriteString("\n## Target normalization preview\n\n")
	for _, item := range report.TargetChanges {
		fmt.Fprintf(&out, "- `%s` → `%s`: %d (%s)\n", redactReportText(item.From), redactReportText(item.To), len(item.IDs), joinIDs(item.IDs))
	}
	if len(report.TargetChanges) == 0 {
		out.WriteString("- No changes.\n")
	}

	out.WriteString("\n## Explicit type alias preview\n\n")
	for _, item := range report.TypeMappings {
		fmt.Fprintf(&out, "- `%s` → `%s`: %d (%s)\n", item.From, item.To, len(item.IDs), joinIDs(item.IDs))
	}

	out.WriteString("\n## Severity and status\n\n")
	fmt.Fprintf(&out, "- Severity: %s\n", formatCounts(report.Severity))
	fmt.Fprintf(&out, "- Status: %s\n", formatCounts(report.Status))
	fmt.Fprintf(&out, "- Open by severity: %s\n", formatCounts(report.OpenBySeverity))
	fmt.Fprintf(&out, "- Open critical: %d\n", report.OpenBySeverity["critical"])
	fmt.Fprintf(&out, "- Open high: %d\n", report.OpenBySeverity["high"])
	fmt.Fprintf(&out, "- Open critical + high: %d\n", report.OpenBySeverity["critical"]+report.OpenBySeverity["high"])

	out.WriteString("\n## Safety statement\n\nThis report is read-only. No row was updated. Empty targets remain empty; severity is not recalculated.\n")
	return out.String()
}

func redactReportText(value string) string {
	for _, pattern := range reportSecretPatterns {
		value = pattern.ReplaceAllString(value, "[REDACTED]")
	}
	return value
}

// SanitizedReport avoids copying recognizable API keys from legacy target
// text into the machine-readable report. IDs still identify every affected row.
func SanitizedReport(report Report) Report {
	report.TargetChanges = append([]TargetChange(nil), report.TargetChanges...)
	for i := range report.TargetChanges {
		report.TargetChanges[i].From = redactReportText(report.TargetChanges[i].From)
		report.TargetChanges[i].To = redactReportText(report.TargetChanges[i].To)
	}
	return report
}

func joinIDs(ids []string) string {
	if len(ids) == 0 {
		return "no affected IDs"
	}
	return "IDs: " + strings.Join(ids, ", ")
}

func formatCounts(values map[string]int) string {
	keys := make([]string, 0, len(values))
	for key := range values {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	parts := make([]string, 0, len(keys))
	for _, key := range keys {
		parts = append(parts, fmt.Sprintf("%s=%d", key, values[key]))
	}
	return strings.Join(parts, ", ")
}
