package handler

import "strings"

// normalizeFofaFields accepts the legacy province return-field alias from saved
// forms and API clients. FOFA exports this value as region. Query syntax and
// other search providers do not pass through this conversion.
func normalizeFofaFields(raw string) string {
	fields := splitAndCleanCSV(raw)
	seen := make(map[string]struct{}, len(fields))
	normalized := make([]string, 0, len(fields))
	for _, field := range fields {
		if field == "province" {
			field = "region"
		}
		if _, ok := seen[field]; ok {
			continue
		}
		seen[field] = struct{}{}
		normalized = append(normalized, field)
	}
	return strings.Join(normalized, ",")
}
