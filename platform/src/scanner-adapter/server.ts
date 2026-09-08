import { createHash, timingSafeEqual } from "node:crypto";

import Fastify, { type FastifyInstance, type FastifyRequest } from "fastify";
import { ZodError } from "zod";

import { executeAwvs } from "./awvs.js";
import type { ScannerAdapterConfig } from "./config.js";
import { Semaphore } from "./http.js";
import { executeToolBackend } from "./tool-backend.js";
import { scannerJobSchema, type ScannerEngine } from "./types.js";
import { selectProxy } from "./proxy-pool.js";

function tokenMatches(actual: string | undefined, expected: string): boolean {
  if (!actual) return false;
  const actualHash = createHash("sha256").update(actual).digest();
  const expectedHash = createHash("sha256").update(expected).digest();
  return timingSafeEqual(actualHash, expectedHash);
}

function bearerToken(request: FastifyRequest): string | undefined {
  const header = request.headers.authorization;
  if (!header?.startsWith("Bearer ")) return undefined;
  const value = header.slice(7).trim();
  return value || undefined;
}

function backendStatus(config: ScannerAdapterConfig) {
  return {
    hexstrike: Boolean(config.backends.hexstrike),
    "kali-mcp": Boolean(config.backends.kali),
    awvs: Boolean(config.backends.awvs && config.backends.awvsApiKey),
  } as const;
}

export async function buildScannerAdapter(
  config: ScannerAdapterConfig,
): Promise<FastifyInstance> {
  const app = Fastify({
    logger: { level: config.logLevel },
    bodyLimit: 2 * 1024 * 1024,
    requestIdHeader: "x-request-id",
    genReqId: () => crypto.randomUUID(),
  });
  const semaphores: Record<ScannerEngine, Semaphore> = {
    hexstrike: new Semaphore(config.maxConcurrentPerEngine),
    "kali-mcp": new Semaphore(config.maxConcurrentPerEngine),
    awvs: new Semaphore(config.maxConcurrentPerEngine),
  };

  // 安全默认：未配置 worker token 时以失败关闭策略运行——所有受保护端点一律拒绝，
  // 避免无认证的扫描执行入口被意外暴露。
  if (!config.adapterToken) {
    app.log.warn(
      "scanner adapter started WITHOUT JYSEC_ENGINE_ADAPTER_TOKEN; protected endpoints will reject every request until a token is configured",
    );
  }

  app.addHook("onRequest", async (request, reply) => {
    if (request.url === "/healthz" || request.url === "/readyz") return;
    if (!tokenMatches(bearerToken(request), config.adapterToken ?? "")) {
      await reply.code(401).send({ error: "unauthorized" });
    }
  });

  app.get("/healthz", async () => ({
    status: "ok",
    backends: backendStatus(config),
    concurrency: Object.fromEntries(
      Object.entries(semaphores).map(([engine, semaphore]) => [engine, semaphore.snapshot()]),
    ),
    proxyPool: { configured: config.proxyPool.length, ids: config.proxyPool.map((item) => item.id) },
  }));

  app.get("/readyz", async (_request, reply) => {
    const backends = backendStatus(config);
    const ready = Object.values(backends).some(Boolean);
    return reply.code(ready ? 200 : 503).send({ status: ready ? "ready" : "unconfigured", backends });
  });

  app.post("/v1/jobs/execute", async (request, reply) => {
    const job = scannerJobSchema.parse(request.body);
    const now = Date.now();
    if (new Date(job.run.authorization.validFrom).getTime() > now) {
      return reply.code(403).send({ error: "authorization_not_yet_valid" });
    }
    if (new Date(job.run.authorization.validUntil).getTime() <= now) {
      return reply.code(403).send({ error: "authorization_expired" });
    }
    const result = await semaphores[job.run.engine].run(async () => {
      const proxy = await selectProxy(config, job.run.id);
      if (job.run.engine === "awvs") {
        if (!job.run.authorization.operations.some((item) =>
          item === "active_scan" || item === "exploit_validation"
        )) {
          throw new Error("AWVS requires active_scan or exploit_validation authorization");
        }
        return executeAwvs(job, config, proxy);
      }
      return executeToolBackend(job.run.engine, job, config, proxy);
    });
    return reply.send(result);
  });

  app.setErrorHandler(async (error, request, reply) => {
    if (error instanceof ZodError) {
      return reply.code(400).send({
        error: "invalid_request",
        issues: error.issues.map((issue) => ({ path: issue.path.join("."), message: issue.message })),
      });
    }
    request.log.error({ err: error }, "scanner adapter request failed");
    return reply.code(502).send({
      error: "scanner_backend_error",
      message: error instanceof Error ? error.message : String(error),
    });
  });

  return app;
}
