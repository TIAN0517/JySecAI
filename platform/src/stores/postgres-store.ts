import { readFile } from "node:fs/promises";

import pg from "pg";

import { DomainError } from "../core/errors.js";
import type { ControlPlaneStore, ListRunsFilter, RunPatch } from "../core/store.js";
import type {
  Artifact,
  AuthorizationScope,
  Finding,
  Page,
  PlanId,
  RunEvent,
  SecurityRun,
  TenantSubscription,
  UsageLedgerEntry,
} from "../core/types.js";

const { Pool } = pg;
type Row = Record<string, unknown>;

function iso(value: unknown): string {
  if (value instanceof Date) return value.toISOString();
  return new Date(String(value)).toISOString();
}

function optionalIso(value: unknown): string | undefined {
  return value === null || value === undefined ? undefined : iso(value);
}

function jsonValue<T>(value: unknown): T {
  return (typeof value === "string" ? JSON.parse(value) : value) as T;
}

function rowToRun(row: Row): SecurityRun {
  const run: SecurityRun = {
    id: String(row.id),
    tenantId: String(row.tenant_id),
    projectId: String(row.project_id),
    actorUserId: String(row.actor_user_id),
    engine: String(row.engine) as SecurityRun["engine"],
    profile: String(row.profile) as SecurityRun["profile"],
    targets: jsonValue<string[]>(row.targets),
    objective: String(row.objective),
    authorization: jsonValue<AuthorizationScope>(row.authorization),
    config: jsonValue<Record<string, unknown>>(row.config),
    status: String(row.status) as SecurityRun["status"],
    estimatedCredits: Number(row.estimated_credits),
    reservedCredits: Number(row.reserved_credits),
    idempotencyKey: String(row.idempotency_key),
    createdAt: iso(row.created_at),
    updatedAt: iso(row.updated_at),
  };
  const statusReason = row.status_reason === null ? undefined : String(row.status_reason);
  const externalRunId = row.external_run_id === null ? undefined : String(row.external_run_id);
  const startedAt = optionalIso(row.started_at);
  const finishedAt = optionalIso(row.finished_at);
  if (statusReason !== undefined) run.statusReason = statusReason;
  if (externalRunId !== undefined) run.externalRunId = externalRunId;
  if (startedAt !== undefined) run.startedAt = startedAt;
  if (finishedAt !== undefined) run.finishedAt = finishedAt;
  return run;
}

function rowToEvent(row: Row): RunEvent {
  const event: RunEvent = {
    id: String(row.id),
    tenantId: String(row.tenant_id),
    runId: String(row.run_id),
    sequence: Number(row.sequence),
    type: String(row.type) as RunEvent["type"],
    at: iso(row.at),
    data: jsonValue<Record<string, unknown>>(row.data),
  };
  if (row.actor_user_id !== null && row.actor_user_id !== undefined) {
    event.actorUserId = String(row.actor_user_id);
  }
  return event;
}

function rowToFinding(row: Row): Finding {
  const finding: Finding = {
    id: String(row.id),
    tenantId: String(row.tenant_id),
    projectId: String(row.project_id),
    runId: String(row.run_id),
    engine: String(row.engine) as Finding["engine"],
    engineVersion: String(row.engine_version),
    category: String(row.category),
    title: String(row.title),
    severity: String(row.severity) as Finding["severity"],
    confidence: Number(row.confidence),
    status: String(row.status) as Finding["status"],
    evidenceRefs: jsonValue<string[]>(row.evidence_refs),
    fingerprint: String(row.fingerprint),
    createdAt: iso(row.created_at),
  };
  if (row.test_case_id !== null) finding.testCaseId = String(row.test_case_id);
  if (row.reproduction_summary !== null) finding.reproductionSummary = String(row.reproduction_summary);
  if (row.counterevidence !== null) finding.counterevidence = String(row.counterevidence);
  if (row.remediation !== null) finding.remediation = String(row.remediation);
  return finding;
}

function rowToArtifact(row: Row): Artifact {
  return {
    id: String(row.id),
    tenantId: String(row.tenant_id),
    projectId: String(row.project_id),
    runId: String(row.run_id),
    kind: String(row.kind),
    objectKey: String(row.object_key),
    sha256: String(row.sha256),
    mediaType: String(row.media_type),
    sizeBytes: Number(row.size_bytes),
    encrypted: Boolean(row.encrypted),
    createdAt: iso(row.created_at),
  };
}

export class PostgresStore implements ControlPlaneStore {
  readonly #pool: pg.Pool;

  constructor(connectionString: string) {
    this.#pool = new Pool({
      connectionString,
      max: 30,
      idleTimeoutMillis: 30_000,
      connectionTimeoutMillis: 5_000,
      statement_timeout: 30_000,
      application_name: "jysec-control-plane",
    });
  }

  async migrate(): Promise<void> {
    const migrationUrl = new URL("../../migrations/001_core.sql", import.meta.url);
    const sql = await readFile(migrationUrl, "utf8");
    await this.#pool.query(sql);
  }

  async close(): Promise<void> {
    await this.#pool.end();
  }

  async withTenantRunLock<T>(tenantId: string, operation: () => Promise<T>): Promise<T> {
    const client = await this.#pool.connect();
    try {
      await client.query("SELECT pg_advisory_lock(hashtextextended($1, 0))", [tenantId]);
      return await operation();
    } finally {
      try {
        await client.query("SELECT pg_advisory_unlock(hashtextextended($1, 0))", [tenantId]);
      } finally {
        client.release();
      }
    }
  }

  async createRun(run: SecurityRun): Promise<{ run: SecurityRun; created: boolean }> {
    const client = await this.#pool.connect();
    try {
      await client.query("BEGIN");
      const inserted = await client.query<Row>(
        `INSERT INTO jy_security_runs (
           id, tenant_id, project_id, actor_user_id, engine, profile, targets, objective,
           "authorization", config, status, estimated_credits, reserved_credits,
           idempotency_key, created_at, updated_at
         ) VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8,$9::jsonb,$10::jsonb,$11,$12,$13,$14,$15,$16)
         ON CONFLICT (tenant_id, idempotency_key) DO NOTHING
         RETURNING *`,
        [
          run.id,
          run.tenantId,
          run.projectId,
          run.actorUserId,
          run.engine,
          run.profile,
          JSON.stringify(run.targets),
          run.objective,
          JSON.stringify(run.authorization),
          JSON.stringify(run.config),
          run.status,
          run.estimatedCredits,
          run.reservedCredits,
          run.idempotencyKey,
          run.createdAt,
          run.updatedAt,
        ],
      );
      if (inserted.rowCount === 1 && inserted.rows[0]) {
        await client.query("COMMIT");
        return { run: rowToRun(inserted.rows[0]), created: true };
      }
      const existing = await client.query<Row>(
        "SELECT * FROM jy_security_runs WHERE tenant_id=$1 AND idempotency_key=$2",
        [run.tenantId, run.idempotencyKey],
      );
      await client.query("COMMIT");
      if (!existing.rows[0]) throw new Error("Idempotent run lookup failed");
      return { run: rowToRun(existing.rows[0]), created: false };
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    } finally {
      client.release();
    }
  }

  async getRunByIdempotencyKey(tenantId: string, idempotencyKey: string): Promise<SecurityRun | null> {
    const result = await this.#pool.query<Row>(
      "SELECT * FROM jy_security_runs WHERE tenant_id=$1 AND idempotency_key=$2",
      [tenantId, idempotencyKey],
    );
    return result.rows[0] ? rowToRun(result.rows[0]) : null;
  }

  async getRun(tenantId: string, runId: string): Promise<SecurityRun | null> {
    const result = await this.#pool.query<Row>(
      "SELECT * FROM jy_security_runs WHERE tenant_id=$1 AND id=$2",
      [tenantId, runId],
    );
    return result.rows[0] ? rowToRun(result.rows[0]) : null;
  }

  async listRuns(filter: ListRunsFilter): Promise<Page<SecurityRun>> {
    const decoded = filter.cursor
      ? Buffer.from(filter.cursor, "base64url").toString("utf8")
      : undefined;
    // 分页游标为 (created_at, id) 复合键，避免相同时间戳的纪录在翻页时被漏掉或重复。
    let cursorDate: Date | undefined;
    let cursorId: string | undefined;
    if (decoded) {
      const legacyDate = new Date(decoded);
      if (!Number.isNaN(legacyDate.getTime())) {
        cursorDate = legacyDate;
      } else {
        let parsed: unknown;
        try {
          parsed = JSON.parse(decoded);
        } catch {
          throw new DomainError("invalid_cursor", "Run cursor is invalid");
        }
        if (
          !Array.isArray(parsed) ||
          typeof parsed[0] !== "string" ||
          typeof parsed[1] !== "string" ||
          Number.isNaN(new Date(parsed[0]).getTime())
        ) {
          throw new DomainError("invalid_cursor", "Run cursor is invalid");
        }
        cursorDate = new Date(parsed[0]);
        cursorId = parsed[1];
      }
    }
    const values: unknown[] = [filter.tenantId];
    const clauses = ["tenant_id=$1"];
    if (filter.projectId) {
      values.push(filter.projectId);
      clauses.push(`project_id=$${values.length}`);
    }
    if (cursorDate && cursorId) {
      values.push(cursorDate.toISOString(), cursorId);
      clauses.push(`(created_at, id) < ($${values.length - 1}, $${values.length})`);
    } else if (cursorDate) {
      values.push(cursorDate.toISOString());
      clauses.push(`created_at < $${values.length}`);
    }
    values.push(filter.limit + 1);
    const result = await this.#pool.query<Row>(
      `SELECT * FROM jy_security_runs WHERE ${clauses.join(" AND ")}
       ORDER BY created_at DESC, id DESC LIMIT $${values.length}`,
      values,
    );
    const hasMore = result.rows.length > filter.limit;
    const selected = result.rows.slice(0, filter.limit).map(rowToRun);
    const last = selected.at(-1);
    return hasMore && last
      ? {
          items: selected,
          nextCursor: Buffer.from(JSON.stringify([last.createdAt, last.id])).toString("base64url"),
        }
      : { items: selected };
  }

  async updateRun(tenantId: string, runId: string, patch: RunPatch): Promise<SecurityRun> {
    const values: unknown[] = [tenantId, runId, patch.updatedAt];
    const assignments = ["updated_at=$3"];
    const add = (column: string, value: unknown) => {
      values.push(value);
      assignments.push(`${column}=$${values.length}`);
    };
    if (patch.status !== undefined) add("status", patch.status);
    if (patch.statusReason !== undefined) add("status_reason", patch.statusReason);
    if (patch.externalRunId !== undefined) add("external_run_id", patch.externalRunId);
    if (patch.startedAt !== undefined) add("started_at", patch.startedAt);
    if (patch.finishedAt !== undefined) add("finished_at", patch.finishedAt);
    if (patch.expectedStatus !== undefined) {
      values.push(patch.expectedStatus);
    }
    const statusGuard = patch.expectedStatus !== undefined ? ` AND status=$${values.length}` : "";
    const result = await this.#pool.query<Row>(
      `UPDATE jy_security_runs SET ${assignments.join(", ")}
       WHERE tenant_id=$1 AND id=$2${statusGuard} RETURNING *`,
      values,
    );
    if (!result.rows[0]) {
      const existing = await this.getRun(tenantId, runId);
      if (!existing) throw new DomainError("run_not_found", "Run was not found", 404);
      throw new DomainError("transition_conflict", "Run status changed before the update completed", 409, {
        expected: patch.expectedStatus,
        actual: existing.status,
      });
    }
    return rowToRun(result.rows[0]);
  }

  async countActiveRuns(tenantId: string): Promise<number> {
    const result = await this.#pool.query<{ count: string }>(
      `SELECT COUNT(*)::text AS count FROM jy_security_runs
       WHERE tenant_id=$1 AND status NOT IN ('completed','failed','cancelled')`,
      [tenantId],
    );
    return Number(result.rows[0]?.count ?? 0);
  }

  async appendEvent(event: Omit<RunEvent, "sequence">): Promise<RunEvent> {
    const client = await this.#pool.connect();
    try {
      await client.query("BEGIN");
      const locked = await client.query(
        "SELECT id FROM jy_security_runs WHERE tenant_id=$1 AND id=$2 FOR UPDATE",
        [event.tenantId, event.runId],
      );
      if (locked.rowCount !== 1) throw new DomainError("run_not_found", "Run was not found", 404);
      const result = await client.query<Row>(
        `INSERT INTO jy_run_events (id, tenant_id, run_id, sequence, type, at, actor_user_id, data)
         SELECT $1,$2,$3,COALESCE(MAX(sequence),0)+1,$4,$5,$6,$7::jsonb
         FROM jy_run_events WHERE tenant_id=$2 AND run_id=$3
         RETURNING *`,
        [
          event.id,
          event.tenantId,
          event.runId,
          event.type,
          event.at,
          event.actorUserId ?? null,
          JSON.stringify(event.data),
        ],
      );
      await client.query("COMMIT");
      if (!result.rows[0]) throw new Error("Event insert did not return a row");
      return rowToEvent(result.rows[0]);
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    } finally {
      client.release();
    }
  }

  async listEvents(
    tenantId: string,
    runId: string,
    afterSequence: number,
    limit: number,
  ): Promise<RunEvent[]> {
    const result = await this.#pool.query<Row>(
      `SELECT * FROM jy_run_events
       WHERE tenant_id=$1 AND run_id=$2 AND sequence>$3
       ORDER BY sequence ASC LIMIT $4`,
      [tenantId, runId, afterSequence, limit],
    );
    return result.rows.map(rowToEvent);
  }

  async appendUsage(entry: UsageLedgerEntry): Promise<{ entry: UsageLedgerEntry; created: boolean }> {
    const result = await this.#pool.query<Row>(
      `INSERT INTO jy_usage_ledger
       (id, tenant_id, run_id, period, kind, credits, idempotency_key, created_at)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
       ON CONFLICT (tenant_id, idempotency_key) DO NOTHING RETURNING *`,
      [
        entry.id,
        entry.tenantId,
        entry.runId,
        entry.period,
        entry.kind,
        entry.credits,
        entry.idempotencyKey,
        entry.createdAt,
      ],
    );
    if (result.rows[0]) return { entry, created: true };
    const existing = await this.#pool.query<Row>(
      "SELECT * FROM jy_usage_ledger WHERE tenant_id=$1 AND idempotency_key=$2",
      [entry.tenantId, entry.idempotencyKey],
    );
    const row = existing.rows[0];
    if (!row) throw new Error("Idempotent usage lookup failed");
    return {
      entry: {
        id: String(row.id),
        tenantId: String(row.tenant_id),
        runId: String(row.run_id),
        period: String(row.period),
        kind: String(row.kind) as UsageLedgerEntry["kind"],
        credits: Number(row.credits),
        idempotencyKey: String(row.idempotency_key),
        createdAt: iso(row.created_at),
      },
      created: false,
    };
  }

  async sumUsage(tenantId: string, period: string): Promise<number> {
    const result = await this.#pool.query<{ total: string }>(
      "SELECT COALESCE(SUM(credits),0)::text AS total FROM jy_usage_ledger WHERE tenant_id=$1 AND period=$2",
      [tenantId, period],
    );
    return Number(result.rows[0]?.total ?? 0);
  }

  async getTenantPlan(tenantId: string): Promise<PlanId> {
    const result = await this.#pool.query<{ plan_id: PlanId }>(
      "SELECT plan_id FROM jy_tenant_subscriptions WHERE tenant_id=$1 AND status='active'",
      [tenantId],
    );
    return result.rows[0]?.plan_id ?? "community";
  }

  async setTenantPlan(tenantId: string, plan: PlanId): Promise<void> {
    await this.#pool.query(
      `INSERT INTO jy_tenant_subscriptions (tenant_id, plan_id)
       VALUES ($1,$2)
       ON CONFLICT (tenant_id) DO UPDATE
       SET plan_id=EXCLUDED.plan_id, status='active', updated_at=NOW()`,
      [tenantId, plan],
    );
  }

  async getSubscription(tenantId: string): Promise<TenantSubscription | null> {
    const result = await this.#pool.query<Row>(
      "SELECT * FROM jy_tenant_subscriptions WHERE tenant_id=$1",
      [tenantId],
    );
    const row = result.rows[0];
    if (!row) return null;
    const subscription: TenantSubscription = {
      tenantId: String(row.tenant_id),
      planId: String(row.plan_id) as PlanId,
      provider: String(row.provider) as TenantSubscription["provider"],
      status: String(row.status),
      updatedAt: iso(row.updated_at),
    };
    if (row.provider_customer_id !== null) subscription.providerCustomerId = String(row.provider_customer_id);
    if (row.provider_subscription_id !== null) subscription.providerSubscriptionId = String(row.provider_subscription_id);
    const currentPeriodEnd = optionalIso(row.current_period_end);
    if (currentPeriodEnd !== undefined) subscription.currentPeriodEnd = currentPeriodEnd;
    return subscription;
  }

  async upsertSubscription(subscription: TenantSubscription): Promise<void> {
    await this.#pool.query(
      `INSERT INTO jy_tenant_subscriptions
       (tenant_id, plan_id, provider, provider_customer_id, provider_subscription_id,
        status, current_period_end, updated_at)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
       ON CONFLICT (tenant_id) DO UPDATE SET
         plan_id=EXCLUDED.plan_id,
         provider=EXCLUDED.provider,
         provider_customer_id=EXCLUDED.provider_customer_id,
         provider_subscription_id=EXCLUDED.provider_subscription_id,
         status=EXCLUDED.status,
         current_period_end=EXCLUDED.current_period_end,
         updated_at=EXCLUDED.updated_at`,
      [
        subscription.tenantId,
        ["active", "trialing"].includes(subscription.status) ? subscription.planId : "community",
        subscription.provider,
        subscription.providerCustomerId ?? null,
        subscription.providerSubscriptionId ?? null,
        subscription.status,
        subscription.currentPeriodEnd ?? null,
        subscription.updatedAt,
      ],
    );
  }

  async upsertFinding(finding: Finding): Promise<Finding> {
    const result = await this.#pool.query<Row>(
      `INSERT INTO jy_findings (
         id, tenant_id, project_id, run_id, engine, engine_version, test_case_id,
         category, title, severity, confidence, status, evidence_refs,
         reproduction_summary, counterevidence, remediation, fingerprint, created_at
       ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::jsonb,$14,$15,$16,$17,$18)
       ON CONFLICT (tenant_id, project_id, fingerprint) DO UPDATE SET
         run_id=EXCLUDED.run_id,
         engine=EXCLUDED.engine,
         engine_version=EXCLUDED.engine_version,
         test_case_id=EXCLUDED.test_case_id,
         category=EXCLUDED.category,
         title=EXCLUDED.title,
         severity=EXCLUDED.severity,
         confidence=EXCLUDED.confidence,
         status=EXCLUDED.status,
         evidence_refs=EXCLUDED.evidence_refs,
         reproduction_summary=EXCLUDED.reproduction_summary,
         counterevidence=EXCLUDED.counterevidence,
         remediation=EXCLUDED.remediation,
         updated_at=NOW()
       RETURNING *`,
      [
        finding.id,
        finding.tenantId,
        finding.projectId,
        finding.runId,
        finding.engine,
        finding.engineVersion,
        finding.testCaseId ?? null,
        finding.category,
        finding.title,
        finding.severity,
        finding.confidence,
        finding.status,
        JSON.stringify(finding.evidenceRefs),
        finding.reproductionSummary ?? null,
        finding.counterevidence ?? null,
        finding.remediation ?? null,
        finding.fingerprint,
        finding.createdAt,
      ],
    );
    if (!result.rows[0]) throw new Error("Finding upsert did not return a row");
    return rowToFinding(result.rows[0]);
  }

  async listProjectFindings(tenantId: string, projectId: string, limit: number): Promise<Finding[]> {
    const result = await this.#pool.query<Row>(
      `SELECT * FROM jy_findings WHERE tenant_id=$1 AND project_id=$2
       ORDER BY created_at DESC, id DESC LIMIT $3`,
      [tenantId, projectId, limit],
    );
    return result.rows.map(rowToFinding);
  }

  async appendArtifact(artifact: Artifact): Promise<{ artifact: Artifact; created: boolean }> {
    const inserted = await this.#pool.query<Row>(
      `INSERT INTO jy_artifacts
       (id, tenant_id, project_id, run_id, kind, object_key, sha256, media_type, size_bytes, encrypted, created_at)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
       ON CONFLICT (tenant_id, object_key) DO NOTHING RETURNING *`,
      [
        artifact.id,
        artifact.tenantId,
        artifact.projectId,
        artifact.runId,
        artifact.kind,
        artifact.objectKey,
        artifact.sha256,
        artifact.mediaType,
        artifact.sizeBytes,
        artifact.encrypted,
        artifact.createdAt,
      ],
    );
    if (inserted.rows[0]) return { artifact: rowToArtifact(inserted.rows[0]), created: true };
    const existing = await this.#pool.query<Row>(
      "SELECT * FROM jy_artifacts WHERE tenant_id=$1 AND object_key=$2",
      [artifact.tenantId, artifact.objectKey],
    );
    if (!existing.rows[0]) throw new Error("Idempotent artifact lookup failed");
    const stored = rowToArtifact(existing.rows[0]);
    if (stored.sha256 !== artifact.sha256 || stored.runId !== artifact.runId) {
      throw new DomainError("artifact_conflict", "Artifact object key already references different evidence", 409);
    }
    return { artifact: stored, created: false };
  }

  async listRunArtifacts(tenantId: string, runId: string, limit: number): Promise<Artifact[]> {
    const result = await this.#pool.query<Row>(
      `SELECT * FROM jy_artifacts WHERE tenant_id=$1 AND run_id=$2
       ORDER BY created_at DESC, id DESC LIMIT $3`,
      [tenantId, runId, limit],
    );
    return result.rows.map(rowToArtifact);
  }
}
