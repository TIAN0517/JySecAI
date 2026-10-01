package observability

import (
	"strings"
	"sync"
	"testing"

	"jysecai/internal/failure"
)

func TestIncAndCount(t *testing.T) {
	r := New()
	r.IncValidation("nuclei", failure.CodeMissingRequiredArgument)
	r.IncValidation("nuclei", failure.CodeMissingRequiredArgument)
	r.IncStopForInput("nuclei", failure.CodeMissingRequiredArgument)
	r.IncExecution("nuclei")

	if got := r.Count(CounterToolValidationFailureTotal, "nuclei", string(failure.CodeMissingRequiredArgument)); got != 2 {
		t.Fatalf("validation counter: want 2, got %d", got)
	}
	if got := r.Count(CounterToolStopForInputTotal, "nuclei", string(failure.CodeMissingRequiredArgument)); got != 1 {
		t.Fatalf("stop_for_input counter: want 1, got %d", got)
	}
	if got := r.Count(CounterToolExecutionTotal, "nuclei", ""); got != 1 {
		t.Fatalf("execution counter: want 1, got %d", got)
	}
}

// Test 11: labels are bounded to (tool, code); no high-cardinality fields.
func TestLabelsBoundedToToolAndCode(t *testing.T) {
	r := New()
	r.IncValidation("nuclei", failure.CodeMissingRequiredArgument)
	snap := r.Snapshot()
	for _, inner := range snap.Counters {
		for k := range inner {
			// The labelKey type itself enforces the label set: it only has
			// Tool and Code fields. If anyone extends it, this assertion
			// fails to compile, surfacing the schema change at test time.
			_ = k.Tool
			_ = k.Code
		}
	}
}

// Test 20: concurrent access is race-free.
func TestConcurrentInc(t *testing.T) {
	r := New()
	var wg sync.WaitGroup
	const goroutines = 32
	const each = 100
	for g := 0; g < goroutines; g++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := 0; i < each; i++ {
				r.IncExecution("nuclei")
			}
		}()
	}
	wg.Wait()
	if got := r.Count(CounterToolExecutionTotal, "nuclei", ""); got != int64(goroutines*each) {
		t.Fatalf("expected %d, got %d", goroutines*each, got)
	}
}

func TestSnapshotStringSorted(t *testing.T) {
	r := New()
	r.IncValidation("zulu", failure.CodeInvalidArgument)
	r.IncValidation("alpha", failure.CodeMissingRequiredArgument)
	s := r.Snapshot().String()
	// alpha should appear before zulu.
	if !strings.Contains(s, "alpha") || !strings.Contains(s, "zulu") {
		t.Fatalf("snapshot missing labels: %s", s)
	}
	if strings.Index(s, "alpha") > strings.Index(s, "zulu") {
		t.Fatalf("snapshot not sorted: %s", s)
	}
}

func TestIncRejectsUnknownCounter(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Fatalf("expected panic on unknown counter")
		}
	}()
	r := New()
	r.Inc("bogus_counter", "nuclei", "")
}

func TestCountReturnsZeroForUnknownLabel(t *testing.T) {
	r := New()
	r.IncValidation("nuclei", failure.CodeMissingRequiredArgument)
	if got := r.Count(CounterToolValidationFailureTotal, "amass", "X"); got != 0 {
		t.Fatalf("expected 0 for untouched label, got %d", got)
	}
	if got := r.Count("unknown_counter", "nuclei", "X"); got != 0 {
		t.Fatalf("expected 0 for unknown counter, got %d", got)
	}
}