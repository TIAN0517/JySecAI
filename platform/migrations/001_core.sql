BEGIN;

CREATE TABLE IF NOT EXISTS jy_tenant_subscriptions (
    tenant_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL CHECK (plan_id IN ('community', 'professional', 'business', 'enterprise')),
    provider TEXT NOT NULL DEFAULT 'manual',
    provider_customer_id TEXT,
    provider_subscription_id TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    current_period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jy_security_runs (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    actor_user_id TEXT NOT NULL,
    engine TEXT NOT NULL,
    profile TEXT NOT NULL,
    targets JSONB NOT NULL,
    objective TEXT NOT NULL,
    authorization JSONB NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL,
    status_reason TEXT,
    estimated_credits INTEGER NOT NULL CHECK (estimated_credits >= 0),
    reserved_credits INTEGER NOT NULL CHECK (reserved_credits >= 0),
    external_run_id TEXT,
    idempotency_key TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_jy_security_runs_tenant_created
    ON jy_security_runs (tenant_id, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_jy_security_runs_project_created
    ON jy_security_runs (tenant_id, project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jy_security_runs_active
    ON jy_security_runs (tenant_id, status)
    WHERE status NOT IN ('completed', 'failed', 'cancelled');

CREATE TABLE IF NOT EXISTS jy_run_events (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    run_id TEXT NOT NULL REFERENCES jy_security_runs(id) ON DELETE CASCADE,
    sequence BIGINT NOT NULL,
    type TEXT NOT NULL,
    at TIMESTAMPTZ NOT NULL,
    actor_user_id TEXT,
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (run_id, sequence)
);

CREATE INDEX IF NOT EXISTS idx_jy_run_events_replay
    ON jy_run_events (tenant_id, run_id, sequence);

CREATE TABLE IF NOT EXISTS jy_usage_ledger (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    run_id TEXT NOT NULL REFERENCES jy_security_runs(id) ON DELETE RESTRICT,
    period TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('reservation', 'debit', 'refund', 'adjustment')),
    credits INTEGER NOT NULL,
    idempotency_key TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_jy_usage_ledger_period
    ON jy_usage_ledger (tenant_id, period);

CREATE TABLE IF NOT EXISTS jy_findings (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    run_id TEXT NOT NULL REFERENCES jy_security_runs(id) ON DELETE CASCADE,
    engine TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    test_case_id TEXT,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    status TEXT NOT NULL CHECK (status IN ('suspected', 'confirmed', 'inconclusive', 'resolved')),
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    reproduction_summary TEXT,
    counterevidence TEXT,
    remediation TEXT,
    fingerprint TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, project_id, fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_jy_findings_project
    ON jy_findings (tenant_id, project_id, severity, created_at DESC);

CREATE TABLE IF NOT EXISTS jy_artifacts (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    run_id TEXT NOT NULL REFERENCES jy_security_runs(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    object_key TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    media_type TEXT NOT NULL,
    size_bytes BIGINT NOT NULL CHECK (size_bytes >= 0),
    encrypted BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, object_key)
);

COMMIT;
