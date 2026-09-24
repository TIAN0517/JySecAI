// Package observability owns the typed counters that the scanner/tool
// runtime emits. Counters are intentionally narrow: cardinality is bounded
// by the failure.Code closed enumeration and the set of registered tool
// names, so adding a metric never requires thinking about per-target labels.
//
// The current implementation is a no-op-friendly registry that downstream
// callers (Prometheus, OTel, structured logs) can subscribe to. The default
// InMemory counter is concurrency-safe and suitable for unit tests.
package observability

import (
	"fmt"
	"sort"
	"strings"
	"sync"
	"sync/atomic"

	"jysecai/internal/failure"
)

// Counter names are defined as constants so observability dashboards and
// alert rules have a stable contract.
const (
	CounterToolValidationFailureTotal = "tool_validation_failure_total"
	CounterToolStopForInputTotal      = "tool_stop_for_input_total"
	CounterToolPolicyDeniedTotal      = "tool_policy_denied_total"
	CounterToolPreflightFailureTotal  = "tool_preflight_failure_total"
	CounterToolExecutionTotal         = "tool_execution_total"
)

// allCounters lists every counter the runtime emits. Used to enumerate
// during tests and to drive the /metrics endpoint when wired up.
var allCounters = []string{
	CounterToolValidationFailureTotal,
	CounterToolStopForInputTotal,
	CounterToolPolicyDeniedTotal,
	CounterToolPreflightFailureTotal,
	CounterToolExecutionTotal,
}

// allowedCounter maps the constant to true; guards against accidental
// typos at Inc() call sites.
var allowedCounter = func() map[string]bool {
	m := make(map[string]bool, len(allCounters))
	for _, c := range allCounters {
		m[c] = true
	}
	return m
}()

// Registry is the central counter registry. The zero value is not usable;
// always construct via New so the underlying maps are initialized.
type Registry struct {
	mu       sync.RWMutex
	counters map[string]*labeledCounter
}

// New returns an empty Registry.
func New() *Registry {
	return &Registry{counters: map[string]*labeledCounter{}}
}

// labeledCounter is a Counter keyed by (label1, label2). The label set is
// intentionally limited to (tool, code) so we never accidentally pull a
// target URL or execution_id into a metric label.
type labeledCounter struct {
	mu sync.RWMutex
	m  map[labelKey]*atomic.Int64
}

// labelKey is the canonical (tool, code) pair.
type labelKey struct {
	Tool string
	Code string
}

// Inc bumps the (tool, code) pair on the named counter. Unknown counters
// are rejected via a panic so a typo cannot silently disappear.
func (r *Registry) Inc(counter, tool string, code string) {
	if !allowedCounter[counter] {
		panic(fmt.Sprintf("observability: unknown counter %q", counter))
	}
	r.mu.RLock()
	lc, ok := r.counters[counter]
	r.mu.RUnlock()
	if !ok {
		r.mu.Lock()
		lc, ok = r.counters[counter]
		if !ok {
			lc = &labeledCounter{m: map[labelKey]*atomic.Int64{}}
			r.counters[counter] = lc
		}
		r.mu.Unlock()
	}
	k := labelKey{Tool: strings.TrimSpace(tool), Code: string(code)}
	lc.mu.RLock()
	v, ok := lc.m[k]
	lc.mu.RUnlock()
	if !ok {
		lc.mu.Lock()
		v, ok = lc.m[k]
		if !ok {
			v = &atomic.Int64{}
			lc.m[k] = v
		}
		lc.mu.Unlock()
	}
	v.Add(1)
}

// IncValidation is a convenience for validation failures.
func (r *Registry) IncValidation(tool string, code failure.Code) {
	r.Inc(CounterToolValidationFailureTotal, tool, string(code))
}

// IncStopForInput is a convenience for STOP_FOR_INPUT events.
func (r *Registry) IncStopForInput(tool string, code failure.Code) {
	r.Inc(CounterToolStopForInputTotal, tool, string(code))
}

// IncPolicyDenied is a convenience for POLICY_DENIED events.
func (r *Registry) IncPolicyDenied(tool string, code failure.Code) {
	r.Inc(CounterToolPolicyDeniedTotal, tool, string(code))
}

// IncPreflightFailure is a convenience for preflight failures.
func (r *Registry) IncPreflightFailure(tool string, code failure.Code) {
	r.Inc(CounterToolPreflightFailureTotal, tool, string(code))
}

// IncExecution is a convenience for successful exec starts.
func (r *Registry) IncExecution(tool string) {
	r.Inc(CounterToolExecutionTotal, tool, "")
}

// Snapshot is a point-in-time copy of every counter, with labels sorted
// deterministically. Used by tests and /metrics scraping.
type Snapshot struct {
	Counters map[string]map[labelKey]int64
}

// Snapshot returns a deep copy of the current counter state.
func (r *Registry) Snapshot() Snapshot {
	r.mu.RLock()
	defer r.mu.RUnlock()
	out := Snapshot{Counters: map[string]map[labelKey]int64{}}
	for counter, lc := range r.counters {
		lc.mu.RLock()
		inner := make(map[labelKey]int64, len(lc.m))
		for k, v := range lc.m {
			inner[k] = v.Load()
		}
		lc.mu.RUnlock()
		out.Counters[counter] = inner
	}
	return out
}

// Count returns the current value of (counter, tool, code). Returns 0 if
// the counter or label pair has not been touched. Exported so tests in
// other packages can assert specific counter values without depending on
// the unexported labelKey type.
func (r *Registry) Count(counter, tool, code string) int64 {
	r.mu.RLock()
	lc, ok := r.counters[counter]
	r.mu.RUnlock()
	if !ok {
		return 0
	}
	k := labelKey{Tool: strings.TrimSpace(tool), Code: code}
	lc.mu.RLock()
	v, ok := lc.m[k]
	lc.mu.RUnlock()
	if !ok {
		return 0
	}
	return v.Load()
}

// String renders the snapshot in a stable, line-oriented format suitable for
// log dumps in test failures.
func (s Snapshot) String() string {
	counters := make([]string, 0, len(s.Counters))
	for c := range s.Counters {
		counters = append(counters, c)
	}
	sort.Strings(counters)
	var b strings.Builder
	for _, c := range counters {
		inner := s.Counters[c]
		keys := make([]labelKey, 0, len(inner))
		for k := range inner {
			keys = append(keys, k)
		}
		sort.Slice(keys, func(i, j int) bool {
			if keys[i].Tool != keys[j].Tool {
				return keys[i].Tool < keys[j].Tool
			}
			return keys[i].Code < keys[j].Code
		})
		for _, k := range keys {
			fmt.Fprintf(&b, "%s{tool=%q,code=%q} %d\n", c, k.Tool, k.Code, inner[k])
		}
	}
	return b.String()
}
