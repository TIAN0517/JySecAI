package handler

import (
	"encoding/csv"
	"fmt"
	"strings"
	"time"

	"jysecai/internal/database"

	"github.com/gin-gonic/gin"
)

// escapeCSVCell neutralises spreadsheet formula injection. Several columns are
// attacker-influenced — chat_uploads records the request body's path as
// ResourceID — so a low-privileged user can plant a payload that a
// higher-privileged auditor executes by opening the export. Prefixing with a
// single quote keeps the text visible while denying Excel/LibreOffice any
// formula interpretation.
func escapeCSVCell(value string) string {
	trimmed := strings.TrimLeft(value, " \t\r\n")
	if trimmed == "" {
		return value
	}
	switch trimmed[0] {
	case '=', '+', '-', '@', '\t', '\r':
		return "'" + value
	}
	return value
}

func writeAuditLogsCSV(c *gin.Context, logs []*database.AuditLog) {
	c.Header("Content-Type", "text/csv; charset=utf-8")
	c.Header("Content-Disposition", fmt.Sprintf(`attachment; filename="audit-logs-%s.csv"`, time.Now().Format("20060102")))

	w := csv.NewWriter(c.Writer)
	_ = w.Write([]string{
		"id", "created_at", "level", "category", "action", "result", "actor",
		"session_hint", "client_ip", "resource_type", "resource_id", "message",
	})
	for _, row := range logs {
		if row == nil {
			continue
		}
		_ = w.Write([]string{
			row.ID,
			row.CreatedAt.UTC().Format(time.RFC3339),
			escapeCSVCell(row.Level),
			escapeCSVCell(row.Category),
			escapeCSVCell(row.Action),
			escapeCSVCell(row.Result),
			escapeCSVCell(row.Actor),
			escapeCSVCell(row.SessionHint),
			escapeCSVCell(row.ClientIP),
			escapeCSVCell(row.ResourceType),
			escapeCSVCell(row.ResourceID),
			escapeCSVCell(row.Message),
		})
	}
	w.Flush()
}
