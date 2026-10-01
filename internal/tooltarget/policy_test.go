package tooltarget

import (
	"testing"

	"jysecai/internal/failure"
)

// Test 9: authorized exact hostname accepted.
func TestAuthorizedExactHostAccepted(t *testing.T) {
	p := NewConfigAuthorizedTargetPolicy()
	p.Replace(Config{Entries: []Entry{{Tool: "nuclei", Host: "example.com", Note: "fixture"}}})
	n, err := Normalize("https://example.com")
	if err != nil {
		t.Fatalf("normalize: %v", err)
	}
	dec := p.Check("nuclei", n)
	if !dec.Allowed {
		t.Fatalf("expected allowed, got %+v", dec)
	}
	if dec.Scope != ScopeExactHost {
		t.Fatalf("expected ScopeExactHost, got %s", dec.Scope)
	}
}

// Test 10: subdomain bypass rejected.
func TestSubdomainBypassRejected(t *testing.T) {
	p := NewConfigAuthorizedTargetPolicy()
	p.Replace(Config{Entries: []Entry{{Tool: "nuclei", Host: "example.com"}}})
	n, err := Normalize("example.com.attacker.invalid")
	if err != nil {
		t.Fatalf("normalize: %v", err)
	}
	dec := p.Check("nuclei", n)
	if dec.Allowed {
		t.Fatalf("expected rejected, got allowed (%+v)", dec)
	}
	if dec.Code != failure.CodeTargetNotAuthorized {
		t.Fatalf("expected TARGET_NOT_AUTHORIZED, got %s", dec.Code)
	}
}

// Test 11: unauthorized host rejected.
func TestUnauthorizedHostRejected(t *testing.T) {
	p := NewConfigAuthorizedTargetPolicy()
	p.Replace(Config{Entries: []Entry{{Tool: "nuclei", Host: "allowed.example"}}})
	n, err := Normalize("https://blocked.example")
	if err != nil {
		t.Fatalf("normalize: %v", err)
	}
	dec := p.Check("nuclei", n)
	if dec.Allowed {
		t.Fatalf("expected rejected, got allowed (%+v)", dec)
	}
}

// Test that exact IP works.
func TestAuthorizedExactIP(t *testing.T) {
	p := NewConfigAuthorizedTargetPolicy()
	p.Replace(Config{Entries: []Entry{{Tool: "nuclei", IP: "192.0.2.10"}}})
	n, err := Normalize("192.0.2.10")
	if err != nil {
		t.Fatalf("normalize: %v", err)
	}
	dec := p.Check("nuclei", n)
	if !dec.Allowed {
		t.Fatalf("expected allowed IP, got %+v", dec)
	}
	if dec.Scope != ScopeExactIP {
		t.Fatalf("expected ScopeExactIP, got %s", dec.Scope)
	}
}

// Test tool-specific vs any-tool entries.
func TestToolScopedVsAnyTool(t *testing.T) {
	p := NewConfigAuthorizedTargetPolicy()
	p.Replace(Config{Entries: []Entry{
		{Tool: "nuclei", Host: "nuc.example"},
		{Host: "shared.example"},
	}})
	nNuc, _ := Normalize("nuc.example")
	nSh, _ := Normalize("shared.example")

	if !p.Check("nuclei", nNuc).Allowed {
		t.Fatalf("tool-specific entry should match")
	}
	if !p.Check("amass", nSh).Allowed {
		t.Fatalf("any-tool entry should match amass")
	}
	if p.Check("amass", nNuc).Allowed {
		t.Fatalf("amass should not match nuclei-specific entry")
	}
}

// Test nil target is reported as INVALID_TARGET, not allowed.
func TestNilTarget(t *testing.T) {
	p := NewConfigAuthorizedTargetPolicy()
	dec := p.Check("nuclei", nil)
	if dec.Allowed {
		t.Fatalf("nil target must not be allowed")
	}
	if dec.Code != failure.CodeInvalidTarget {
		t.Fatalf("expected INVALID_TARGET, got %s", dec.Code)
	}
}
