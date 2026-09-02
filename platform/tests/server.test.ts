import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { loadConfig } from "../src/config.js";
import type { ControlPlaneStore } from "../src/core/store.js";
import { buildServer } from "../src/http/server.js";
import { MemoryRunDispatcher } from "../src/infra/dispatcher.js";
import { MemoryStore } from "../src/stores/memory-store.js";

describe("JySecAI HTTP API", () => {
  let app: Awaited<ReturnType<typeof buildServer>>;
  let store: ControlPlaneStore;

  beforeEach(async () => {
    const config = loadConfig({
      NODE_ENV: "test",
      JYSEC_DEV_AUTH: "true",
      JYSEC_JWT_SECRET: "test-secret-that-is-at-least-32-bytes",
      JYSEC_JOB_SIGNING_SECRET: "test-worker-secret-at-least-32-bytes",
      JYSEC_STORE: "memory",
    });
    store = new MemoryStore();
    await store.setTenantPlan("test-tenant", "business");
    app = await buildServer({ config, store, dispatcher: new MemoryRunDispatcher() });
  });

  afterEach(async () => {
    await app.close();
  });

  it("serves health without authentication", async () => {
    const response = await app.inject({ method: "GET", url: "/healthz" });
    expect(response.statusCode).toBe(200);
    expect(response.json()).toMatchObject({ product: "JySecAI", developer: "Jy 技術團隊" });
  });

  it("reports truthful runtime engine availability", async () => {
    const response = await app.inject({
      method: "GET",
      url: "/v1/catalog",
      headers: {
        "x-jysec-tenant": "test-tenant",
        "x-jysec-user": "owner",
        "x-jysec-roles": "owner",
      },
    });
    expect(response.statusCode).toBe(200);
    const engines = Object.fromEntries(
      response.json().engines.map((engine: { id: string }) => [engine.id, engine]),
    );
    expect(engines.strix).toMatchObject({ active: true, status: "ready" });
    expect(engines.cyberstrike).toMatchObject({
      active: false,
      status: "unconfigured",
      reason: "CYBERSTRIKE_SERVICE_TOKEN is required to authenticate with the workflow service.",
    });
    expect(engines.promptfoo).toMatchObject({
      active: false,
      status: "unconfigured",
      reason: "JYSEC_ENGINE_PROMPTFOO_URL must be set to the adapter service URL.",
    });
  });

  it("serves a CSP-safe governance console with a route back to the full console", async () => {
    const response = await app.inject({ method: "GET", url: "/" });

    expect(response.statusCode).toBe(200);
    expect(response.headers["content-security-policy"]).toContain("script-src 'self'");
    expect(response.headers["content-security-policy"]).not.toContain("script-src 'self' 'unsafe-inline'");
    expect(response.body).toContain('id="console-button"');
    expect(response.body).toContain('href="/"');
    expect(response.body).toContain("完整作戰主控台");
  });

  it("keeps tenant run listings isolated", async () => {
    const auth = {
      "x-jysec-tenant": "test-tenant",
      "x-jysec-user": "owner",
      "x-jysec-roles": "owner,security_approver",
    };
    const createResponse = await app.inject({
      method: "POST",
      url: "/v1/runs",
      headers: auth,
      payload: {
        projectId: "project-1",
        engine: "strix",
        profile: "quick",
        targets: ["https://app.example.com"],
        objective: "Authorized application security validation",
        authorization: {
          id: "AUTH-HTTP-0001",
          projectId: "project-1",
          tenantId: "test-tenant",
          targetPatterns: ["*.example.com"],
          operations: ["active_scan"],
          validFrom: new Date(Date.now() - 60_000).toISOString(),
          validUntil: new Date(Date.now() + 86_400_000).toISOString(),
          approvedBy: "owner@example.com",
          attested: true,
        },
        config: {},
        idempotencyKey: "http-idempotency-0001",
      },
    });
    expect(createResponse.statusCode).toBe(202);

    const own = await app.inject({ method: "GET", url: "/v1/runs", headers: auth });
    expect(own.json().items).toHaveLength(1);

    const other = await app.inject({
      method: "GET",
      url: "/v1/runs",
      headers: { ...auth, "x-jysec-tenant": "other-tenant" },
    });
    expect(other.json().items).toHaveLength(0);
  });

  it("protects metrics when a metrics token is configured", async () => {
    await app.close();
    const config = loadConfig({
      NODE_ENV: "test",
      JYSEC_DEV_AUTH: "true",
      JYSEC_JWT_SECRET: "test-secret-that-is-at-least-32-bytes",
      JYSEC_JOB_SIGNING_SECRET: "test-worker-secret-at-least-32-bytes",
      JYSEC_METRICS_TOKEN: "test-metrics-token-that-is-at-least-32-bytes",
      JYSEC_STORE: "memory",
    });
    store = new MemoryStore();
    app = await buildServer({ config, store, dispatcher: new MemoryRunDispatcher() });

    expect((await app.inject({ method: "GET", url: "/metrics" })).statusCode).toBe(401);
    expect(
      (
        await app.inject({
          method: "GET",
          url: "/metrics",
          headers: { authorization: "Bearer test-metrics-token-that-is-at-least-32-bytes" },
        })
      ).statusCode,
    ).toBe(200);
  });

  it("fails closed for malformed and unsigned bearer tokens", async () => {
    await app.close();
    const config = loadConfig({
      NODE_ENV: "test",
      JYSEC_DEV_AUTH: "false",
      JYSEC_JWT_SECRET: "test-secret-that-is-at-least-32-bytes",
      JYSEC_JOB_SIGNING_SECRET: "test-worker-secret-at-least-32-bytes",
      JYSEC_STORE: "memory",
    });
    store = new MemoryStore();
    app = await buildServer({ config, store, dispatcher: new MemoryRunDispatcher() });

    const malformed = await app.inject({
      method: "GET",
      url: "/v1/runs",
      headers: { authorization: "Bearer definitely-not-a-jwt" },
    });
    expect(malformed.statusCode).toBe(401);
    expect(malformed.json()).toMatchObject({ error: { code: "invalid_token" } });

    const unsigned = await app.inject({
      method: "GET",
      url: "/v1/runs",
      headers: {
        authorization:
          "Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhdHRhY2tlciIsInRlbmFudF9pZCI6InRlc3QtdGVuYW50In0.",
      },
    });
    expect(unsigned.statusCode).toBe(401);
    expect(unsigned.json()).toMatchObject({ error: { code: "invalid_token" } });
  });
});
