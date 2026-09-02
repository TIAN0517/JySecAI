import { describe, expect, it } from "vitest";

import { loadConfig } from "../src/config.js";

describe("production configuration guardrails", () => {
  it("rejects transient storage and development secrets in production", () => {
    expect(() =>
      loadConfig({
        NODE_ENV: "production",
        JYSEC_STORE: "memory",
        JYSEC_PUBLIC_BASE_URL: "http://jysec.example.com",
      }),
    ).toThrow();
  });

  it("accepts an isolated production secret set and HTTPS public URL", () => {
    const config = loadConfig({
      NODE_ENV: "production",
      JYSEC_STORE: "postgres",
      DATABASE_URL: "postgres://jysec:test@postgres:5432/jysec",
      JYSEC_PUBLIC_BASE_URL: "https://jysec.example.com",
      JYSEC_INTERNAL_CALLBACK_BASE_URL: "http://control-plane:8787",
      JYSEC_JWT_SECRET: "jwt-secret-production-value-at-least-32-bytes",
      JYSEC_JOB_SIGNING_SECRET: "job-secret-production-value-at-least-32-bytes",
      JYSEC_METRICS_TOKEN: "metrics-production-value-at-least-32-bytes",
      JYSEC_DEV_AUTH: "false",
    });
    expect(config.store).toBe("postgres");
    expect(config.publicBaseUrl).toBe("https://jysec.example.com");
    expect(config.internalCallbackBaseUrl).toBe("http://control-plane:8787");
  });

  it("accepts a remote JWKS identity provider without a shared JWT secret", () => {
    const config = loadConfig({
      NODE_ENV: "production",
      JYSEC_STORE: "postgres",
      DATABASE_URL: "postgres://jysec:test@postgres:5432/jysec",
      JYSEC_PUBLIC_BASE_URL: "https://jysec.example.com",
      JYSEC_JWKS_URL: "https://identity.example.com/.well-known/jwks.json",
      JYSEC_JWT_ISSUER: "https://identity.example.com/",
      JYSEC_JWT_AUDIENCE: "jysec-production",
      JYSEC_JOB_SIGNING_SECRET: "job-secret-production-value-at-least-32-bytes",
      JYSEC_METRICS_TOKEN: "metrics-production-value-at-least-32-bytes",
      JYSEC_DEV_AUTH: "false",
    });

    expect(config.jwksUrl).toBe("https://identity.example.com/.well-known/jwks.json");
    expect(config.jwtIssuer).toBe("https://identity.example.com/");
    expect(config.jwtAudience).toBe("jysec-production");
  });
});
