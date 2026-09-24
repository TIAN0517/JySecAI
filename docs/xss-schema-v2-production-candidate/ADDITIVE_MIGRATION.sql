-- REVIEW ONLY. Apply only to the verified legacy rich schema after Phase 1B approval.
-- Production execution is NOT authorized by Phase 1A.
-- The Go migration checks existing columns and executes only missing ADD COLUMN statements.
BEGIN IMMEDIATE;
ALTER TABLE xss_payloads ADD COLUMN callback_token TEXT;
ALTER TABLE xss_payloads ADD COLUMN enabled INTEGER NOT NULL DEFAULT 1;
ALTER TABLE xss_payloads ADD COLUMN domain TEXT NOT NULL DEFAULT '';
ALTER TABLE xss_payloads ADD COLUMN domain_only INTEGER NOT NULL DEFAULT 0;
ALTER TABLE xss_payloads ADD COLUMN owner_user_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_xss_payloads_callback_token ON xss_payloads(callback_token) WHERE callback_token IS NOT NULL AND callback_token <> '';
CREATE INDEX IF NOT EXISTS idx_xss_payloads_created_at ON xss_payloads(created_at);
CREATE INDEX IF NOT EXISTS idx_xss_captures_created_at ON xss_captures(created_at);
CREATE INDEX IF NOT EXISTS idx_xss_captures_payload_id ON xss_captures(payload_id);
COMMIT;
