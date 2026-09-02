import { DomainError } from "../core/errors.js";
import type { ControlPlaneStore, ListRunsFilter, RunPatch } from "../core/store.js";
import type {
  Artifact,
  Finding,
  Page,
  PlanId,
  RunEvent,
  SecurityRun,
  TenantSubscription,
  UsageLedgerEntry,
} from "../core/types.js";

const terminalStatuses = new Set<SecurityRun["status"]>(["completed", "failed", "cancelled"]);

function copy<T>(value: T): T {
  return structuredClone(value);
}

export class MemoryStore implements ControlPlaneStore {
  readonly #runs = new Map<string, SecurityRun>();
  readonly #idempotency = new Map<string, string>();
  readonly #events = new Map<string, RunEvent[]>();
  readonly #usage = new Map<string, UsageLedgerEntry>();
  readonly #plans = new Map<string, PlanId>();
  readonly #subscriptions = new Map<string, TenantSubscription>();
  readonly #findings = new Map<string, Finding>();
  readonly #artifacts = new Map<string, Artifact>();
  readonly #tenantRunLocks = new Map<string, Promise<void>>();

  async migrate(): Promise<void> {}

  async close(): Promise<void> {}

  async withTenantRunLock<T>(tenantId: string, operation: () => Promise<T>): Promise<T> {
    const previous = this.#tenantRunLocks.get(tenantId) ?? Promise.resolve();
    let release = (): void => {};
    const current = new Promise<void>((resolve) => {
      release = resolve;
    });
    const tail = previous.then(() => current);
    this.#tenantRunLocks.set(tenantId, tail);
    await previous;
    try {
      return await operation();
    } finally {
      release();
      if (this.#tenantRunLocks.get(tenantId) === tail) this.#tenantRunLocks.delete(tenantId);
    }
  }

  async createRun(run: SecurityRun): Promise<{ run: SecurityRun; created: boolean }> {
    const idempotencyIndex = `${run.tenantId}:${run.idempotencyKey}`;
    const existingId = this.#idempotency.get(idempotencyIndex);
    if (existingId) {
      const existing = this.#runs.get(existingId);
      if (!existing) throw new Error("Corrupt in-memory idempotency index");
      return { run: copy(existing), created: false };
    }
    this.#runs.set(run.id, copy(run));
    this.#idempotency.set(idempotencyIndex, run.id);
    return { run: copy(run), created: true };
  }

  async getRunByIdempotencyKey(tenantId: string, idempotencyKey: string): Promise<SecurityRun | null> {
    const runId = this.#idempotency.get(`${tenantId}:${idempotencyKey}`);
    if (!runId) return null;
    const run = this.#runs.get(runId);
    return run?.tenantId === tenantId ? copy(run) : null;
  }

  async getRun(tenantId: string, runId: string): Promise<SecurityRun | null> {
    const run = this.#runs.get(runId);
    return run?.tenantId === tenantId ? copy(run) : null;
  }

  async listRuns(filter: ListRunsFilter): Promise<Page<SecurityRun>> {
    const ordered = [...this.#runs.values()]
      .filter((run) => run.tenantId === filter.tenantId)
      .filter((run) => !filter.projectId || run.projectId === filter.projectId)
      .sort((left, right) => right.createdAt.localeCompare(left.createdAt));
    const offset = filter.cursor ? Number.parseInt(Buffer.from(filter.cursor, "base64url").toString("utf8"), 10) : 0;
    const start = Number.isFinite(offset) && offset >= 0 ? offset : 0;
    const items = ordered.slice(start, start + filter.limit).map(copy);
    const next = start + items.length;
    return next < ordered.length
      ? { items, nextCursor: Buffer.from(String(next)).toString("base64url") }
      : { items };
  }

  async updateRun(tenantId: string, runId: string, patch: RunPatch): Promise<SecurityRun> {
    const current = this.#runs.get(runId);
    if (!current || current.tenantId !== tenantId) {
      throw new DomainError("run_not_found", "Run was not found", 404);
    }
    if (patch.expectedStatus !== undefined && current.status !== patch.expectedStatus) {
      throw new DomainError("transition_conflict", "Run status changed before the update completed", 409, {
        expected: patch.expectedStatus,
        actual: current.status,
      });
    }
    const updated: SecurityRun = { ...current, updatedAt: patch.updatedAt };
    if (patch.status !== undefined) updated.status = patch.status;
    if (patch.statusReason !== undefined) updated.statusReason = patch.statusReason;
    if (patch.externalRunId !== undefined) updated.externalRunId = patch.externalRunId;
    if (patch.startedAt !== undefined) updated.startedAt = patch.startedAt;
    if (patch.finishedAt !== undefined) updated.finishedAt = patch.finishedAt;
    this.#runs.set(runId, updated);
    return copy(updated);
  }

  async countActiveRuns(tenantId: string): Promise<number> {
    return [...this.#runs.values()].filter(
      (run) => run.tenantId === tenantId && !terminalStatuses.has(run.status),
    ).length;
  }

  async appendEvent(event: Omit<RunEvent, "sequence">): Promise<RunEvent> {
    const key = `${event.tenantId}:${event.runId}`;
    const current = this.#events.get(key) ?? [];
    const created: RunEvent = { ...event, sequence: current.length + 1 };
    current.push(copy(created));
    this.#events.set(key, current);
    return copy(created);
  }

  async listEvents(
    tenantId: string,
    runId: string,
    afterSequence: number,
    limit: number,
  ): Promise<RunEvent[]> {
    return (this.#events.get(`${tenantId}:${runId}`) ?? [])
      .filter((event) => event.sequence > afterSequence)
      .slice(0, limit)
      .map(copy);
  }

  async appendUsage(entry: UsageLedgerEntry): Promise<{ entry: UsageLedgerEntry; created: boolean }> {
    const key = `${entry.tenantId}:${entry.idempotencyKey}`;
    const existing = this.#usage.get(key);
    if (existing) return { entry: copy(existing), created: false };
    this.#usage.set(key, copy(entry));
    return { entry: copy(entry), created: true };
  }

  async sumUsage(tenantId: string, period: string): Promise<number> {
    return [...this.#usage.values()]
      .filter((entry) => entry.tenantId === tenantId && entry.period === period)
      .reduce((total, entry) => total + entry.credits, 0);
  }

  async getTenantPlan(tenantId: string): Promise<PlanId> {
    return this.#plans.get(tenantId) ?? "community";
  }

  async setTenantPlan(tenantId: string, plan: PlanId): Promise<void> {
    this.#plans.set(tenantId, plan);
  }

  async getSubscription(tenantId: string): Promise<TenantSubscription | null> {
    const subscription = this.#subscriptions.get(tenantId);
    return subscription ? copy(subscription) : null;
  }

  async upsertSubscription(subscription: TenantSubscription): Promise<void> {
    this.#subscriptions.set(subscription.tenantId, copy(subscription));
    if (["active", "trialing"].includes(subscription.status)) {
      this.#plans.set(subscription.tenantId, subscription.planId);
    } else {
      this.#plans.set(subscription.tenantId, "community");
    }
  }

  async upsertFinding(finding: Finding): Promise<Finding> {
    const key = `${finding.tenantId}:${finding.projectId}:${finding.fingerprint}`;
    const existing = this.#findings.get(key);
    const stored = existing
      ? { ...copy(finding), id: existing.id, createdAt: existing.createdAt }
      : copy(finding);
    this.#findings.set(key, stored);
    return copy(stored);
  }

  async listProjectFindings(tenantId: string, projectId: string, limit: number): Promise<Finding[]> {
    return [...this.#findings.values()]
      .filter((finding) => finding.tenantId === tenantId && finding.projectId === projectId)
      .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
      .slice(0, limit)
      .map(copy);
  }

  async appendArtifact(artifact: Artifact): Promise<{ artifact: Artifact; created: boolean }> {
    const key = `${artifact.tenantId}:${artifact.objectKey}`;
    const existing = this.#artifacts.get(key);
    if (existing) return { artifact: copy(existing), created: false };
    this.#artifacts.set(key, copy(artifact));
    return { artifact: copy(artifact), created: true };
  }

  async listRunArtifacts(tenantId: string, runId: string, limit: number): Promise<Artifact[]> {
    return [...this.#artifacts.values()]
      .filter((artifact) => artifact.tenantId === tenantId && artifact.runId === runId)
      .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
      .slice(0, limit)
      .map(copy);
  }
}
