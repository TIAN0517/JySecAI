package recon

import "time"

// Phase identifies the ordered stages of a reconnaissance run.
type Phase string

const (
	PhaseDiscovery Phase = "discovery"
	PhaseServices  Phase = "services"
	PhaseDeep      Phase = "deep"
	PhaseEnhance   Phase = "enhance"
)

// Asset is a normalized observation produced by a collector.
type Asset struct {
	Type       string            `json:"type"`
	Value      string            `json:"value"`
	Source     string            `json:"source"`
	Metadata   map[string]string `json:"metadata,omitempty"`
	ObservedAt time.Time         `json:"observed_at"`
}

// CollectorResult is deliberately explicit: failed tools are never reported as successful scans.
type CollectorResult struct {
	Name       string    `json:"name"`
	Phase      Phase     `json:"phase"`
	Status     string    `json:"status"`
	Summary    string    `json:"summary,omitempty"`
	Error      string    `json:"error,omitempty"`
	Assets     []Asset   `json:"assets,omitempty"`
	StartedAt  time.Time `json:"started_at"`
	FinishedAt time.Time `json:"finished_at"`
}

type Run struct {
	ID         string            `json:"id"`
	Target     string            `json:"target"`
	Profile    string            `json:"profile"`
	Status     string            `json:"status"`
	StartedAt  time.Time         `json:"started_at"`
	FinishedAt *time.Time        `json:"finished_at,omitempty"`
	Results    []CollectorResult `json:"results"`
}
