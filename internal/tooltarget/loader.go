package tooltarget

import "jysecai/internal/config"

// FromConfigAuthorizedTargets adapts the config-layer scanner
// authorized-target entries into the tooltarget package's internal Entry
// shape. Entries with neither Host nor IP are dropped (they would be
// unusable at Check time).
//
// The function is a pure adapter; callers MUST NOT mutate the result.
func FromConfigAuthorizedTargets(in []config.ScannerAuthorizedTarget) []Entry {
	if len(in) == 0 {
		return nil
	}
	out := make([]Entry, 0, len(in))
	for _, src := range in {
		entry := Entry{
			Tool: src.Tool,
			Host: src.Host,
			IP:   src.IP,
			Note: src.Note,
		}
		if entry.Host == "" && entry.IP == "" {
			continue
		}
		out = append(out, entry)
	}
	return out
}