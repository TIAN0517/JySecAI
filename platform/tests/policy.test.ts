import { describe, expect, it } from "vitest";

import { engineCatalog } from "../src/core/catalog.js";
import { evaluateRunPolicy } from "../src/core/policy.js";
import type { AuthorizationScope } from "../src/core/types.js";

const now = new Date("2026-09-02T12:00:00.000Z");

function scope(overrides: Partial<AuthorizationScope> = {}): AuthorizationScope {
  return {
    id: "AUTH-TEST-0001",
    projectId: "project-1",
    tenantId: "tenant-1",
    targetPatterns: ["*.example.com", "10.20.0.0/16"],
    operations: ["active_scan"],
    validFrom: "2026-09-01T00:00:00.000Z",
    validUntil: "2026-09-10T00:00:00.000Z",
    approvedBy: "owner@example.com",
    attested: true,
    ...overrides,
  };
}

describe("evaluateRunPolicy", () => {
  it("accepts authorized wildcard domains and CIDR addresses", () => {
    const decision = evaluateRunPolicy({
      tenantId: "tenant-1",
      projectId: "project-1",
      descriptor: engineCatalog.strix,
      profile: "standard",
      targets: ["https://api.example.com/v1", "10.20.44.8"],
      authorization: scope(),
      now,
    });

    expect(decision.allowed).toBe(true);
    expect(decision.approvalRequired).toBe(true);
    expect(decision.normalizedTargets).toHaveLength(2);
  });

  it("does not let a wildcard match the domain apex", () => {
    const decision = evaluateRunPolicy({
      tenantId: "tenant-1",
      projectId: "project-1",
      descriptor: engineCatalog.strix,
      profile: "quick",
      targets: ["example.com"],
      authorization: scope(),
      now,
    });

    expect(decision.allowed).toBe(false);
    expect(decision.reasons.join(" ")).toContain("outside authorized scope");
  });

  it("rejects expired and cross-tenant authorization", () => {
    const decision = evaluateRunPolicy({
      tenantId: "tenant-1",
      projectId: "project-1",
      descriptor: engineCatalog.strix,
      profile: "quick",
      targets: ["api.example.com"],
      authorization: scope({ tenantId: "tenant-2", validUntil: "2026-09-02T11:59:59.000Z" }),
      now,
    });

    expect(decision.allowed).toBe(false);
    expect(decision.reasons).toContain("authorization tenant mismatch");
    expect(decision.reasons).toContain("authorization has expired");
  });

  it("allows read-only AD audit without a second execution approval", () => {
    const decision = evaluateRunPolicy({
      tenantId: "tenant-1",
      projectId: "project-1",
      descriptor: engineCatalog["ad-audit"],
      profile: "audit",
      targets: ["dc01.example.com"],
      authorization: scope({ operations: ["credential_audit"] }),
      now,
    });

    expect(decision.allowed).toBe(true);
    expect(decision.approvalRequired).toBe(false);
  });
});
