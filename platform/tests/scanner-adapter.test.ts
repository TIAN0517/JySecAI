import http, { type IncomingMessage, type ServerResponse } from "node:http";

import { afterEach, describe, expect, it } from "vitest";

import { loadScannerAdapterConfig } from "../src/scanner-adapter/config.js";
import { buildScannerAdapter } from "../src/scanner-adapter/server.js";
import { executeToolBackend } from "../src/scanner-adapter/tool-backend.js";
import { scannerJobSchema, type ScannerEngine, type ScannerJob } from "../src/scanner-adapter/types.js";
import type { ScopeOperation } from "../src/core/types.js";

interface MockRequest {
  method: string;
  path: string;
  body: unknown;
}

const servers: http.Server[] = [];
const apps: Array<Awaited<ReturnType<typeof buildScannerAdapter>>> = [];

afterEach(async () => {
  await Promise.all(apps.splice(0).map((app) => app.close()));
  await Promise.all(servers.splice(0).map((server) => new Promise<void>((resolve) => server.close(() => resolve()))));
});

async function body(request: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];
  for await (const chunk of request) chunks.push(Buffer.from(chunk));
  const raw = Buffer.concat(chunks).toString("utf8");
  return raw ? JSON.parse(raw) as unknown : {};
}

function json(response: ServerResponse, status: number, value: unknown, headers: Record<string, string> = {}) {
  response.writeHead(status, { "content-type": "application/json", ...headers });
  response.end(JSON.stringify(value));
}

async function mockServer(
  handler: (request: MockRequest, response: ServerResponse) => void,
): Promise<{ origin: string; requests: MockRequest[] }> {
  const requests: MockRequest[] = [];
  const server = http.createServer(async (request, response) => {
    const entry = {
      method: request.method ?? "GET",
      path: request.url ?? "/",
      body: await body(request),
    };
    requests.push(entry);
    handler(entry, response);
  });
  servers.push(server);
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("mock server did not bind");
  return { origin: `http://127.0.0.1:${address.port}`, requests };
}

function job(
  engine: ScannerEngine,
  operations: ScopeOperation[],
  config: Record<string, unknown>,
): ScannerJob {
  return scannerJobSchema.parse({
    schemaVersion: 1,
    run: {
      id: "run-scanner-001",
      tenantId: "tenant-a",
      projectId: "project-a",
      engine,
      profile: "quick",
      targets: ["https://example.test"],
      objective: "Authorized integration verification",
      authorization: {
        id: "AUTH-TEST-001",
        targetPatterns: ["example.test"],
        operations,
        validFrom: new Date(Date.now() - 60_000).toISOString(),
        validUntil: new Date(Date.now() + 60_000).toISOString(),
        attested: true,
      },
      config,
    },
  });
}

function adapterConfig(values: Record<string, string>) {
  return loadScannerAdapterConfig({
    JYSEC_SCANNER_MAX_RETRIES: "0",
    JYSEC_SCANNER_REQUEST_TIMEOUT_SECONDS: "5",
    ...values,
  });
}

describe("tool scanner backends", () => {
  it("normalizes and confirms a finding only after an authorized validation task", async () => {
    const upstream = await mockServer((request, response) => {
      if (request.path === "/api/tools/nmap") {
        json(response, 200, {
          findings: [{ title: "Reflected XSS", category: "xss", severity: "high" }],
        });
        return;
      }
      if (request.path === "/api/tools/nuclei") {
        json(response, 200, {
          findings: [{ title: "Reflected XSS", category: "xss", severity: "high" }],
        });
        return;
      }
      json(response, 404, { error: "not found" });
    });
    const result = await executeToolBackend(
      "kali-mcp",
      job("kali-mcp", ["exploit_validation"], {
        autoValidate: true,
        tasks: [{ tool: "nmap", parameters: {}, targetMode: "each", successMarkers: [] }],
        validationTasks: [{ tool: "nuclei", parameters: {}, targetMode: "each", successMarkers: [] }],
      }),
      adapterConfig({ JYSEC_KALI_API_URL: upstream.origin }),
    );

    expect(upstream.requests.map((item) => item.path)).toEqual([
      "/api/tools/nmap",
      "/api/tools/nuclei",
    ]);
    expect(result.findings).toHaveLength(1);
    expect(result.findings[0]?.status).toBe("confirmed");
    expect(result.summary.validationTasksExecuted).toBe(1);
  });

  it("does not execute validation tasks without exploit_validation authorization", async () => {
    const upstream = await mockServer((_request, response) => {
      json(response, 200, {
        findings: [{ title: "TLS weakness", category: "tls", severity: "medium" }],
      });
    });
    const result = await executeToolBackend(
      "hexstrike",
      job("hexstrike", ["active_scan"], {
        autoValidate: true,
        tasks: [{ tool: "nmap", parameters: {}, targetMode: "each", successMarkers: [] }],
        validationTasks: [{ tool: "nuclei", parameters: {}, targetMode: "each", successMarkers: [] }],
      }),
      adapterConfig({ JYSEC_HEXSTRIKE_API_URL: upstream.origin }),
    );

    expect(upstream.requests).toHaveLength(1);
    expect(result.findings[0]?.status).toBe("suspected");
    expect(result.summary.validationAuthorized).toBe(false);
  });
});


describe("scanner adapter HTTP boundary", () => {
  it("keeps health public and protects execution with the configured bearer token", async () => {
    const app = await buildScannerAdapter(adapterConfig({
      JYSEC_ENGINE_ADAPTER_TOKEN: "adapter-secret",
      JYSEC_HEXSTRIKE_API_URL: "http://127.0.0.1:9999",
    }));
    apps.push(app);

    expect((await app.inject({ method: "GET", url: "/healthz" })).statusCode).toBe(200);
    const response = await app.inject({
      method: "POST",
      url: "/v1/jobs/execute",
      payload: job("hexstrike", ["active_scan"], {}),
    });
    expect(response.statusCode).toBe(401);
    expect(response.json()).toEqual({ error: "unauthorized" });
  });
});
