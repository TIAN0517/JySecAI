package handler

import (
	"encoding/json"
	"strings"
	"testing"

	"jysecai/internal/config"
	"jysecai/internal/database"

	"gopkg.in/yaml.v3"
)

// Old DNS configuration and request fields are deliberately unsupported. No
// hostname below is contacted: this test only inspects synthetic output.
func TestXSSDeprecatedDNSConfigurationCannotEnableDNSCallback(t *testing.T) {
	var cfg config.XssConfig
	if err := yaml.Unmarshal([]byte("enabled: true\nbind_host: 127.0.0.1\nbind_port: 18877\ndns_exfil_domain: disabled.invalid\n"), &cfg); err != nil {
		t.Fatal(err)
	}
	db := xssTestDB(t)
	r := xssTestRouter(db, cfg, xssSession("synthetic-owner"))
	w := xssRequest(r, "POST", "/api/xss/payloads/generate", `{"name":"phase1a1-test","source_url":"http://127.0.0.1/test","dns_exfil_domain":"disabled.invalid"}`)
	if w.Code != 200 {
		t.Fatalf("HTTP callback generation status: %d", w.Code)
	}
	var result struct {
		Payload   database.XSSPayload `json:"payload"`
		BeaconURL string              `json:"beacon_url"`
	}
	if err := json.Unmarshal(w.Body.Bytes(), &result); err != nil {
		t.Fatal(err)
	}
	payload, err := db.GetXSSPayload(result.Payload.ID)
	if err != nil {
		t.Fatal(err)
	}
	if result.BeaconURL != "http://127.0.0.1:18877/api/xss/capture" || !strings.Contains(payload.Script, result.BeaconURL) {
		t.Fatal("callback must remain the configured HTTP endpoint")
	}
	for _, forbidden := range []string{"disabled.invalid", "dns_exfil", "new Image", "btoa("} {
		if strings.Contains(payload.Script, forbidden) {
			t.Fatalf("unsupported DNS generation marker: %s", forbidden)
		}
	}
	configResponse := xssRequest(r, "GET", "/api/xss/config", "")
	if strings.Contains(configResponse.Body.String(), "dns_exfil") {
		t.Fatal("DNS field exposed in management contract")
	}
	serialized, err := json.Marshal(cfg)
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(string(serialized), "dns_exfil") {
		t.Fatal("DNS field still supported by runtime config")
	}
}

func TestXSSFreshSchemaHasRichIDsAndNoDNSColumn(t *testing.T) {
	db := xssTestDB(t)
	for _, table := range []string{"xss_payloads", "xss_captures"} {
		rows, err := db.Query("PRAGMA table_info(" + table + ")")
		if err != nil {
			t.Fatal(err)
		}
		foundID := false
		for rows.Next() {
			var cid, notnull, pk int
			var name, typ string
			var defaultValue interface{}
			if err := rows.Scan(&cid, &name, &typ, &notnull, &defaultValue, &pk); err != nil {
				rows.Close()
				t.Fatal(err)
			}
			if name == "dns_exfil_domain" {
				rows.Close()
				t.Fatal("DNS column recreated")
			}
			if name == "id" {
				foundID = typ == "TEXT"
			}
		}
		if err := rows.Err(); err != nil {
			rows.Close()
			t.Fatal(err)
		}
		rows.Close()
		if !foundID {
			t.Fatalf("%s must use TEXT IDs", table)
		}
	}
}
