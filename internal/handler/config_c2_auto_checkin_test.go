package handler

import (
	"encoding/json"
	"testing"

	"jysecai/internal/config"

	"gopkg.in/yaml.v3"
)

func TestUpdateC2ConfigWritesAutoCheckin(t *testing.T) {
	doc := newEmptyYAMLDocument()
	enabled := true
	sleep := 8
	jitter := 20
	stale := 90
	cfg := config.C2Config{
		Enabled: &enabled,
		AutoCheckin: &config.C2AutoCheckinConfig{
			Enabled:              &enabled,
			DefaultSleepSeconds:  &sleep,
			DefaultJitterPercent: &jitter,
			StaleSessionTimeoutSeconds: &stale,
			Listeners: []config.C2AutoListenerConfig{
				{Name: "auto-http", Type: "http_beacon", BindHost: "0.0.0.0", BindPort: 8899, Enabled: &enabled},
			},
		},
	}
	updateC2Config(doc, cfg)

	out, err := yaml.Marshal(doc)
	if err != nil {
		t.Fatalf("yaml.Marshal: %v", err)
	}
	var parsed config.Config
	if err := yaml.Unmarshal(out, &parsed); err != nil {
		t.Fatalf("yaml.Unmarshal rewritten config: %v\n%s", err, string(out))
	}
	ac := parsed.C2.AutoCheckin
	if ac == nil {
		t.Fatal("rewritten config lost auto_checkin section")
	}
	if !ac.EnabledEffective() || !ac.AutoStartListenersEffective() {
		t.Fatalf("rewritten auto_checkin effective = enabled:%v auto_start:%v", ac.EnabledEffective(), ac.AutoStartListenersEffective())
	}
	if ac.DefaultSleepSecondsEffective() != 8 ||
		ac.DefaultJitterPercentEffective() != 20 ||
		ac.StaleSessionTimeoutSecondsEffective() != 90 {
		t.Fatalf("rewritten auto_checkin defaults = %+v", parsed.C2.AutoCheckin)
	}
	auto := ac.EnabledAutoListeners()
	if len(auto) != 1 || auto[0].Name != "auto-http" || auto[0].BindPort != 8899 {
		t.Fatalf("rewritten auto listeners = %+v", auto)
	}
}

func TestUpdateC2ConfigWritesDefaultsWhenAutoCheckinAbsent(t *testing.T) {
	doc := newEmptyYAMLDocument()
	updateC2Config(doc, config.C2Config{})

	out, err := yaml.Marshal(doc)
	if err != nil {
		t.Fatalf("yaml.Marshal: %v", err)
	}
	var parsed config.Config
	if err := yaml.Unmarshal(out, &parsed); err != nil {
		t.Fatalf("yaml.Unmarshal: %v\n%s", err, string(out))
	}
	ac := parsed.C2.AutoCheckin
	if ac == nil {
		t.Fatal("rewritten config should expose auto_checkin defaults")
	}
	if !ac.EnabledEffective() || !ac.AutoStartListenersEffective() {
		t.Fatal("absent auto_checkin should default to enabled + auto start")
	}
	if got := ac.DefaultSleepSecondsEffective(); got != 5 {
		t.Fatalf("default sleep = %d, want 5", got)
	}
	if len(ac.EnabledAutoListeners()) != 0 {
		t.Fatalf("auto listeners = %+v, want empty", ac.EnabledAutoListeners())
	}
}

func TestC2PublicIncludesAutoCheckinJSON(t *testing.T) {
	enabled := true
	sleep := 6
	pub := config.C2Config{
		Enabled: &enabled,
		AutoCheckin: &config.C2AutoCheckinConfig{
			Enabled:             &enabled,
			DefaultSleepSeconds: &sleep,
		},
	}.Public()
	buf, err := json.Marshal(pub)
	if err != nil {
		t.Fatal(err)
	}
	var obj map[string]interface{}
	if err := json.Unmarshal(buf, &obj); err != nil {
		t.Fatal(err)
	}
	if !pub.Enabled || !pub.AutoCheckin.Enabled {
		t.Fatal("C2Public should reflect enabled state")
	}
	if pub.AutoCheckin.DefaultSleepSeconds != 6 {
		t.Fatalf("public default sleep = %d, want 6", pub.AutoCheckin.DefaultSleepSeconds)
	}
	ac, ok := obj["auto_checkin"].(map[string]interface{})
	if !ok {
		t.Fatalf("public JSON missing auto_checkin: %s", string(buf))
	}
	if ac["enabled"] != true || ac["listener_count"] != float64(0) {
		t.Fatalf("public JSON auto_checkin = %+v", ac)
	}
}