import { createHash, randomUUID } from "node:crypto";

import { engineCatalog, estimateRunCredits, planCatalog } from "../core/catalog.js";
import { DomainError } from "../core/errors.js";
import { evaluateRunPolicy } from "../core/policy.js";
import type { ControlPlaneStore } from "../core/store.js";
import type {
  ActorContext,
  Artifact,
  ArtifactSubmission,
  CreateRunInput,
  Finding,
  FindingSubmission,
  RunEventType,
  RunStatus,
  SecurityRun,
  UsageLedgerEntry,
} from "../core/types.js";
import type { RunDispatcher } from "../infra/dispatcher.js";

const terminalStatuses = new Set<RunStatus>(["completed", "failed", "cancelled"]);
const transitionMap: Readonly<Record<RunStatus, readonly RunStatus[]>> = Object.freeze({
  awaiting_approval: ["queued", "cancelled"],
  queued: ["dispatching", "cancelled", "failed"],
  dispatching: ["running", "cancelled", "failed"],
  running: ["paused", "budget_paused", "completed", "cancelled", "failed"],
  paused: ["queued", "cancelled", "failed"],
  budget_paused: ["queued", "cancelled", "failed"],
  completed: [],
  failed: [],
  cancelled: [],
});

function billingPeriod(now = new Date()): string {
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
}

function objectKeySegment(value: string): string {
  return encodeURIComponent(value);
}

const runOperatorRoles = new Set(["owner", "admin", "security_operator", "red_team_operator"]);
const runApproverRoles = new Set(["owner", "admin", "security_approver"]);

function hasAnyRole(actor: ActorContext, allowed: ReadonlySet<string>): boolean {
  return actor.roles.some((role) => allowed.has(role));
}

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, item]) => [key, canonicalize(item)]),
    );
  }
  return value;
}

function sameRunRequest(existing: SecurityRun, input: CreateRunInput, normalizedTargets: string[]): boolean {
  return JSON.stringify(
    canonicalize({
      projectId: existing.projectId,
      engine: existing.engine,
      profile: existing.profile,
      targets: existing.targets,
      objective: existing.objective,
      authorization: existing.authorization,
      config: existing.config,
    }),
  ) === JSON.stringify(
    canonicalize({
      projectId: input.projectId,
      engine: input.engine,
      profile: input.profile,
      targets: normalizedTargets,
      objective: input.objective,
      authorization: input.authorization,
      config: input.config,
    }),
  );
}

export class RunService {
  readonly #store: ControlPlaneStore;
  readonly #dispatcher: RunDispatcher;

  constructor(store: ControlPlaneStore, dispatcher: RunDispatcher) {
    this.#store = store;
    this.#dispatcher = dispatcher;
  }

  async create(actor: ActorContext, input: CreateRunInput): Promise<SecurityRun> {
    if (!hasAnyRole(actor, runOperatorRoles)) {
      throw new DomainError("run_create_denied", "A security operator role is required", 403);
    }
    const descriptor = engineCatalog[input.engine];
    if (!descriptor.active) throw new DomainError("engine_disabled", "The requested engine is disabled", 409);

    const decision = evaluateRunPolicy({
      tenantId: actor.tenantId,
      projectId: input.projectId,
      descriptor,
      profile: input.profile,
      targets: input.targets,
      authorization: input.authorization,
    });
    if (!decision.allowed) {
      throw new DomainError("scope_denied", "Run is outside the authorized engagement scope", 403, {
        reasons: decision.reasons,
      });
    }

    const estimatedCredits = estimateRunCredits(input.engine, input.profile, decision.normalizedTargets.length);
    const created = await this.#store.withTenantRunLock(actor.tenantId, async () => {
      const existing = await this.#store.getRunByIdempotencyKey(actor.tenantId, input.idempotencyKey);
      if (existing) {
        if (!sameRunRequest(existing, input, decision.normalizedTargets)) {
          throw new DomainError(
            "idempotency_conflict",
            "The idempotency key was already used for a different run request",
            409,
          );
        }
        await this.#ensureReservation(existing);
        return { run: existing, created: false };
      }

      const persistedPlan = await this.#store.getTenantPlan(actor.tenantId);
      const plan = planCatalog[persistedPlan];
      if (!plan.engines.includes(input.engine)) {
        throw new DomainError("plan_engine_denied", "Your plan does not include this engine", 402, {
          plan: plan.id,
          engine: input.engine,
        });
      }

      const activeRuns = await this.#store.countActiveRuns(actor.tenantId);
      if (activeRuns >= plan.maxConcurrentRuns) {
        throw new DomainError("concurrency_limit", "Concurrent run limit reached", 429, {
          activeRuns,
          limit: plan.maxConcurrentRuns,
        });
      }

      const period = billingPeriod();
      const usage = await this.#store.sumUsage(actor.tenantId, period);
      if (usage + estimatedCredits > plan.monthlyCredits) {
        throw new DomainError("credit_limit", "Monthly run credits are exhausted", 402, {
          used: usage,
          requested: estimatedCredits,
          limit: plan.monthlyCredits,
        });
      }

      const now = new Date().toISOString();
      const candidate: SecurityRun = {
        id: `run_${randomUUID().replaceAll("-", "")}`,
        tenantId: actor.tenantId,
        projectId: input.projectId,
        actorUserId: actor.userId,
        engine: input.engine,
        profile: input.profile,
        targets: decision.normalizedTargets,
        objective: input.objective,
        authorization: input.authorization,
        config: input.config,
        status: decision.approvalRequired ? "awaiting_approval" : "queued",
        estimatedCredits,
        reservedCredits: estimatedCredits,
        idempotencyKey: input.idempotencyKey,
        createdAt: now,
        updatedAt: now,
      };
      const result = await this.#store.createRun(candidate);
      if (!sameRunRequest(result.run, input, decision.normalizedTargets)) {
        throw new DomainError(
          "idempotency_conflict",
          "The idempotency key was concurrently used for a different run request",
          409,
        );
      }
      await this.#ensureReservation(result.run);
      return result;
    });
    if (!created.created) return created.run;
    const run = created.run;

    await this.#event(run, "run.created", actor.userId, {
      engine: run.engine,
      profile: run.profile,
      targets: run.targets,
      authorizationId: run.authorization.id,
      reservedCredits: run.reservedCredits,
    });

    if (run.status === "awaiting_approval") {
      await this.#event(run, "approval.required", actor.userId, {
        requiredOperation: descriptor.requiredOperation,
      });
    } else {
      await this.#queue(run, actor.userId);
    }
    return run;
  }

  async approve(actor: ActorContext, runId: string): Promise<SecurityRun> {
    if (!hasAnyRole(actor, runApproverRoles)) {
      throw new DomainError("approval_denied", "A security approver role is required", 403);
    }
    const run = await this.requireRun(actor.tenantId, runId);
    if (run.status !== "awaiting_approval") {
      throw new DomainError("invalid_transition", "Run is not awaiting approval", 409);
    }
    const decision = evaluateRunPolicy({
      tenantId: actor.tenantId,
      projectId: run.projectId,
      descriptor: engineCatalog[run.engine],
      profile: run.profile,
      targets: run.targets,
      authorization: run.authorization,
    });
    if (!decision.allowed) {
      throw new DomainError("scope_denied", "Run authorization is no longer valid", 403, {
        reasons: decision.reasons,
      });
    }
    const now = new Date().toISOString();
    const queued = await this.#store.updateRun(actor.tenantId, runId, {
      status: "queued",
      updatedAt: now,
      expectedStatus: "awaiting_approval",
    });
    await this.#event(queued, "approval.granted", actor.userId, {
      authorizationId: run.authorization.id,
    });
    await this.#queue(queued, actor.userId);
    return queued;
  }

  async cancel(actor: ActorContext, runId: string): Promise<SecurityRun> {
    const run = await this.requireRun(actor.tenantId, runId);
    const mayCancel = run.actorUserId === actor.userId || hasAnyRole(actor, runOperatorRoles);
    if (!mayCancel) throw new DomainError("run_cancel_denied", "Run cancellation is not permitted", 403);
    if (terminalStatuses.has(run.status)) return run;
    this.#assertTransition(run.status, "cancelled");
    await this.#dispatcher.requestCancellation(run);
    const now = new Date().toISOString();
    const cancelled = await this.#store.updateRun(actor.tenantId, runId, {
      status: "cancelled",
      statusReason: "Cancelled by an authorized user",
      updatedAt: now,
      finishedAt: now,
      expectedStatus: run.status,
    });
    await this.#event(cancelled, "run.cancelled", actor.userId, {});
    return cancelled;
  }

  async workerTransition(input: {
    tenantId: string;
    runId: string;
    status: RunStatus;
    reason?: string;
    externalRunId?: string;
    data?: Record<string, unknown>;
  }): Promise<SecurityRun> {
    const run = await this.requireRun(input.tenantId, input.runId);
    if (run.status === input.status) return run;
    this.#assertTransition(run.status, input.status);
    const now = new Date().toISOString();
    const patch = {
      status: input.status,
      updatedAt: now,
      ...(input.reason !== undefined ? { statusReason: input.reason } : {}),
      ...(input.externalRunId !== undefined ? { externalRunId: input.externalRunId } : {}),
      ...(!run.startedAt && ["dispatching", "running"].includes(input.status) ? { startedAt: now } : {}),
      ...(terminalStatuses.has(input.status) ? { finishedAt: now } : {}),
    };
    const updated = await this.#store.updateRun(input.tenantId, input.runId, {
      ...patch,
      expectedStatus: run.status,
    });
    const eventType: RunEventType =
      input.status === "dispatching"
        ? "run.dispatching"
        : input.status === "running"
          ? "run.started"
          : input.status === "completed"
            ? "run.completed"
            : input.status === "cancelled"
              ? "run.cancelled"
              : input.status === "paused" || input.status === "budget_paused"
                ? "run.paused"
                : "run.failed";
    await this.#event(updated, eventType, undefined, input.data ?? {});
    return updated;
  }

  async workerEvent(input: {
    tenantId: string;
    runId: string;
    type: "run.progress";
    data: Record<string, unknown>;
  }): Promise<void> {
    const run = await this.requireRun(input.tenantId, input.runId);
    if (terminalStatuses.has(run.status)) {
      throw new DomainError("run_terminal", "A terminal run cannot accept new worker events", 409);
    }
    await this.#event(run, input.type, undefined, input.data);
  }

  async publishFinding(
    tenantId: string,
    runId: string,
    submission: FindingSubmission,
  ): Promise<Finding> {
    const run = await this.#requireWritableWorkerRun(tenantId, runId);
    const fingerprint = createHash("sha256")
      .update(
        JSON.stringify(
          canonicalize({
            engine: run.engine,
            supplied: submission.fingerprint,
            testCaseId: submission.testCaseId,
            category: submission.category,
            title: submission.title,
          }),
        ),
      )
      .digest("hex");
    const finding: Finding = {
      id: `finding_${randomUUID().replaceAll("-", "")}`,
      tenantId: run.tenantId,
      projectId: run.projectId,
      runId: run.id,
      engine: run.engine,
      engineVersion: submission.engineVersion,
      category: submission.category,
      title: submission.title,
      severity: submission.severity,
      confidence: submission.confidence,
      status: submission.status,
      evidenceRefs: submission.evidenceRefs,
      fingerprint,
      createdAt: new Date().toISOString(),
      ...(submission.testCaseId !== undefined ? { testCaseId: submission.testCaseId } : {}),
      ...(submission.reproductionSummary !== undefined
        ? { reproductionSummary: submission.reproductionSummary }
        : {}),
      ...(submission.counterevidence !== undefined ? { counterevidence: submission.counterevidence } : {}),
      ...(submission.remediation !== undefined ? { remediation: submission.remediation } : {}),
    };
    const stored = await this.#store.upsertFinding(finding);
    await this.#event(run, "finding.published", undefined, {
      findingId: stored.id,
      fingerprint: stored.fingerprint,
      severity: stored.severity,
      status: stored.status,
      evidenceRefs: stored.evidenceRefs,
    });
    return stored;
  }

  async publishArtifact(
    tenantId: string,
    runId: string,
    submission: ArtifactSubmission,
  ): Promise<Artifact> {
    const run = await this.#requireWritableWorkerRun(tenantId, runId);
    const relativeKey = submission.objectKey.trim();
    if (
      relativeKey.startsWith("/") ||
      relativeKey.includes("\\") ||
      relativeKey.split("/").some((segment) => segment === ".." || segment === ".")
    ) {
      throw new DomainError("invalid_artifact_key", "Artifact object key must be a safe relative key", 400);
    }
    const artifact: Artifact = {
      id: `artifact_${randomUUID().replaceAll("-", "")}`,
      tenantId: run.tenantId,
      projectId: run.projectId,
      runId: run.id,
      kind: submission.kind,
      objectKey: `tenants/${objectKeySegment(run.tenantId)}/projects/${objectKeySegment(run.projectId)}/runs/${objectKeySegment(run.id)}/${relativeKey}`,
      sha256: submission.sha256,
      mediaType: submission.mediaType,
      sizeBytes: submission.sizeBytes,
      encrypted: submission.encrypted,
      createdAt: new Date().toISOString(),
    };
    const stored = await this.#store.appendArtifact(artifact);
    if (stored.created) {
      await this.#event(run, "artifact.published", undefined, {
        artifactId: stored.artifact.id,
        kind: stored.artifact.kind,
        sha256: stored.artifact.sha256,
        sizeBytes: stored.artifact.sizeBytes,
      });
    }
    return stored.artifact;
  }

  async listProjectFindings(tenantId: string, projectId: string, limit: number): Promise<Finding[]> {
    return this.#store.listProjectFindings(tenantId, projectId, limit);
  }

  async listRunArtifacts(tenantId: string, runId: string, limit: number): Promise<Artifact[]> {
    await this.requireRun(tenantId, runId);
    return this.#store.listRunArtifacts(tenantId, runId, limit);
  }

  async requireRun(tenantId: string, runId: string): Promise<SecurityRun> {
    const run = await this.#store.getRun(tenantId, runId);
    if (!run) throw new DomainError("run_not_found", "Run was not found", 404);
    return run;
  }

  async #requireWritableWorkerRun(tenantId: string, runId: string): Promise<SecurityRun> {
    const run = await this.requireRun(tenantId, runId);
    if (!new Set<RunStatus>(["dispatching", "running"]).has(run.status)) {
      throw new DomainError("run_not_writable", "Evidence can only be published by an active worker run", 409);
    }
    return run;
  }

  async #ensureReservation(run: SecurityRun): Promise<void> {
    const reservation: UsageLedgerEntry = {
      id: `usage_${randomUUID().replaceAll("-", "")}`,
      tenantId: run.tenantId,
      runId: run.id,
      period: billingPeriod(new Date(run.createdAt)),
      kind: "reservation",
      credits: run.reservedCredits,
      idempotencyKey: `run-reservation:${run.id}`,
      createdAt: run.createdAt,
    };
    await this.#store.appendUsage(reservation);
  }

  #assertTransition(current: RunStatus, next: RunStatus): void {
    if (!transitionMap[current].includes(next)) {
      throw new DomainError(
        "invalid_transition",
        `Run cannot transition from ${current} to ${next}`,
        409,
      );
    }
  }

  async #queue(run: SecurityRun, actorUserId?: string): Promise<void> {
    await this.#dispatcher.enqueue(run);
    await this.#event(run, "run.queued", actorUserId, { engine: run.engine });
  }

  async #event(
    run: SecurityRun,
    type: RunEventType,
    actorUserId: string | undefined,
    data: Record<string, unknown>,
  ): Promise<void> {
    await this.#store.appendEvent({
      id: `evt_${randomUUID().replaceAll("-", "")}`,
      tenantId: run.tenantId,
      runId: run.id,
      type,
      at: new Date().toISOString(),
      ...(actorUserId !== undefined ? { actorUserId } : {}),
      data,
    });
  }
}
