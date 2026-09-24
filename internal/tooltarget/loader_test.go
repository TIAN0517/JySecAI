package tooltarget

import (
	"testing"

	"jysecai/internal/config"
)

func TestFromConfigAuthorizedTargetsEmpty(t *testing.T) {
	if got := FromConfigAuthorizedTargets(nil); got != nil {
		t.Fatalf("nil in should produce nil out, got %v", got)
	}
	if got := FromConfigAuthorizedTargets([]config.ScannerAuthorizedTarget{}); got != nil {
		t.Fatalf("empty in should produce nil out, got %v", got)
	}
}

func TestFromConfigAuthorizedTargetsDropsEmpty(t *testing.T) {
	in := []config.ScannerAuthorizedTarget{
		{Tool: "", Host: "", IP: "", Note: "ignored"},
		{Tool: "nuclei", Host: "example.com"},
		{Tool: "nuclei", IP: "192.0.2.10"},
	}
	got := FromConfigAuthorizedTargets(in)
	if len(got) != 2 {
		t.Fatalf("expected 2 valid entries, got %d (%+v)", len(got), got)
	}
	if got[0].Host != "example.com" || got[0].Tool != "nuclei" {
		t.Fatalf("entry[0]: want nuclei/example.com, got %+v", got[0])
	}
	if got[1].IP != "192.0.2.10" {
		t.Fatalf("entry[1]: want ip 192.0.2.10, got %+v", got[1])
	}
}

func TestFromConfigAuthorizedTargetsPreservesFields(t *testing.T) {
	in := []config.ScannerAuthorizedTarget{
		{Tool: "nuclei", Host: "example.com", Note: "fixture"},
	}
	got := FromConfigAuthorizedTargets(in)
	if len(got) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(got))
	}
	if got[0].Tool != "nuclei" || got[0].Host != "example.com" || got[0].Note != "fixture" {
		t.Fatalf("field loss: %+v", got[0])
	}
}