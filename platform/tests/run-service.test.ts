import { beforeEach, describe, expect, it } from "vitest";

import { loadConfig } from "../src/config.js";
import { createRuntimeEngineCatalog } from "../src/core/catalog.js";
import { DomainError } from "../src/core/errors.js";
import type { ActorContext, CreateRunInput } from "../src/core/types.js";
import { MemoryRunDispatcher } from "../src/infra/dispatcher.js";
import { RunService } from "../src/services/run-service.js";
import { MemoryStore } from "../src/stores/memory-store.js";

const actor: ActorContext = {
  tenantId: "tenant-1",
  userId: "user-1",
  roles: ["owner", "security_approver"],
  plan: "business",
  requestId: "request-1",
};

function input(overrides: Partial<CreateRunInput> = {}): CreateRunInput {
  return {
    projectId: "project-1",
    engine: "strix",
    profile: "quick",
    targets: ["https://staging.example.com"],
    objective: "Validate the authorized staging application",
    authorization: {
      id: "AUTH-TEST-0001",
      projectId: "project-1",
      tenantId: "tenant-1",
      targetPatterns: ["*.example.com"],
      operations: ["active_scan"],
      validFrom: new Date(Date.now() - 60_000).toISOString(),
      validUntil: new Date(Date.now() + 86_400_000).toISOString(),
      approvedBy: "owner@example.com",
      attested: true,
    },
    config: {},
    idempotencyKey: "idem-test-0001",
    ...overrides,
  };
}

describe("RunService", () => {
  let store: MemoryStore;
  let dispatcher: MemoryRunDispatcher;
  let service: RunService;

  beforeEach(async () => {
    store = new MemoryStore();
    dispatcher = new MemoryRunDispatcher();
    const config = loadConfig({
      NODE_ENV: "test",
      JYSEC_ENGINE_AD_AUDIT_URL: "http://ad-audit.test:8090",
    });
    service = new RunService(store, dispatcher, createRuntimeEngineCatalog(config));
    await store.setTenantPlan(actor.tenantId, "business");
  });

  it("creates an active run behind HITL and dispatches only after approval", async () => {
    const run = await service.create(actor, input());
    expect(run.status).toBe("awaiting_approval");
    expect(dispatcher.queued).toHaveLength(0);

    const approved = await service.approve(actor, run.id);
    expect(approved.status).toBe("queued");
    expect(dispatcher.queued).toHaveLength(1);

    const events = await store.listEvents(actor.tenantId, run.id, 0, 20);
    expect(events.map((event) => event.type)).toEqual([
      "run.created",
      "approval.required",
      "approval.granted",
      "run.queued",
    ]);
  });

  it("is idempotent and reserves usage only once", async () => {
    const request = input();
    const first = await service.create(actor, request);
    const second = await service.create(actor, request);
    expect(second.id).toBe(first.id);
    expect(await store.sumUsage(actor.tenantId, new Date().toISOString().slice(0, 7))).toBe(
      first.reservedCredits,
    );
  });

  it("rejects reuse of an idempotency key with a different request", async () => {
    const request = input();
    await service.create(actor, request);
    await expect(
      service.create(actor, { ...request, objective: "A different authorized objective" }),
    ).rejects.toMatchObject<Partial<DomainError>>({ code: "idempotency_conflict", statusCode: 409 });
  });

  it("revalidates the authorization window before approval", async () => {
    const request = input({
      authorization: {
        ...input().authorization,
        validUntil: new Date(Date.now() + 25).toISOString(),
      },
    });
    const run = await service.create(actor, request);
    await new Promise((resolve) => setTimeout(resolve, 35));
    await expect(service.approve(actor, run.id)).rejects.toMatchObject<Partial<DomainError>>({
      code: "scope_denied",
      statusCode: 403,
    });
  });

  it("requires a security operator role to create a run", async () => {
    await expect(
      service.create({ ...actor, roles: ["viewer"] }, input()),
    ).rejects.toMatchObject<Partial<DomainError>>({ code: "run_create_denied", statusCode: 403 });
  });

  it("queues authorized read-only AD audits immediately", async () => {
    const run = await service.create(
      actor,
      input({
        engine: "ad-audit",
        profile: "audit",
        targets: ["dc01.example.com"],
        authorization: {
          ...input().authorization,
          operations: ["credential_audit"],
        },
        idempotencyKey: "idem-test-ad-audit",
      }),
    );
    expect(run.status).toBe("queued");
    expect(dispatcher.queued).toHaveLength(1);
  });

  it("blocks engines not included in a tenant plan", async () => {
    await store.setTenantPlan(actor.tenantId, "community");
    await expect(service.create(actor, input())).rejects.toMatchObject<Partial<DomainError>>({
      code: "plan_engine_denied",
      statusCode: 402,
    });
  });

  it("rejects an engine whose runtime adapter is not configured", async () => {
    await expect(
      service.create(
        actor,
        input({ engine: "promptfoo", idempotencyKey: "idem-unconfigured-promptfoo" }),
      ),
    ).rejects.toMatchObject<Partial<DomainError>>({
      code: "engine_unconfigured",
      statusCode: 409,
      details: {
        engine: "promptfoo",
        status: "unconfigured",
        reason: "JYSEC_ENGINE_PROMPTFOO_URL must be set to the adapter service URL.",
      },
    });
    expect((await store.listRuns({ tenantId: actor.tenantId, limit: 20 })).items).toHaveLength(0);
  });

  it("does not allow an ordinary operator to approve", async () => {
    const run = await service.create(actor, input());
    await expect(
      service.approve({ ...actor, roles: ["operator"] }, run.id),
    ).rejects.toMatchObject<Partial<DomainError>>({ code: "approval_denied" });
  });

  it("persists normalized findings and immutable artifact evidence", async () => {
    const run = await service.create(actor, input());
    await service.approve(actor, run.id);
    await service.workerTransition({ tenantId: actor.tenantId, runId: run.id, status: "dispatching" });
    await service.workerTransition({ tenantId: actor.tenantId, runId: run.id, status: "running" });

    const finding = await service.publishFinding(actor.tenantId, run.id, {
      engineVersion: "1.0.0",
      testCaseId: "TC-001",
      category: "access-control",
      title: "Verified authorization boundary weakness",
      severity: "high",
      confidence: 0.97,
      status: "confirmed",
      evidenceRefs: ["evidence/request-response.json"],
      reproductionSummary: "Validated inside the approved staging scope.",
      fingerprint: "adapter-fingerprint-001",
    });
    const artifact = await service.publishArtifact(actor.tenantId, run.id, {
      kind: "http-transcript",
      objectKey: "evidence/request-response.json",
      sha256: "a".repeat(64),
      mediaType: "application/json",
      sizeBytes: 512,
      encrypted: true,
    });

    expect(finding.engine).toBe("strix");
    expect(finding.fingerprint).toMatch(/^[a-f0-9]{64}$/u);
    expect(artifact.objectKey).toContain(`/runs/${run.id}/evidence/request-response.json`);
    expect(await service.listProjectFindings(actor.tenantId, run.projectId, 20)).toHaveLength(1);
    expect(await service.listRunArtifacts(actor.tenantId, run.id, 20)).toHaveLength(1);
    const events = await store.listEvents(actor.tenantId, run.id, 0, 30);
    expect(events.map((event) => event.type)).toContain("finding.published");
    expect(events.map((event) => event.type)).toContain("artifact.published");
  });
});
