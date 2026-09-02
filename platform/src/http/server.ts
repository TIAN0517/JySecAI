import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import cors from "@fastify/cors";
import helmet from "@fastify/helmet";
import rateLimit from "@fastify/rate-limit";
import fastifyStatic from "@fastify/static";
import { collectDefaultMetrics, Counter, Registry } from "@prometheus-io/client";
import Fastify, { type FastifyInstance } from "fastify";
import rawBody from "fastify-raw-body";
import { z, ZodError } from "zod";

import type { AppConfig } from "../config.js";
import { createRuntimeEngineCatalog, planCatalog } from "../core/catalog.js";
import { DomainError, errorMessage } from "../core/errors.js";
import type { ControlPlaneStore } from "../core/store.js";
import {
  artifactSubmissionSchema,
  createRunSchema,
  findingSubmissionSchema,
  planIdSchema,
  runStatusSchema,
} from "../core/types.js";
import type { RunDispatcher } from "../infra/dispatcher.js";
import { RunService } from "../services/run-service.js";
import { BillingService } from "../services/billing-service.js";
import { bearerTokenMatches, buildAuthenticator, requireActor, workerTokenMatches } from "./auth.js";

export interface ServerDependencies {
  config: AppConfig;
  store: ControlPlaneStore;
  dispatcher: RunDispatcher;
}

const runTransitionSchema = z
  .object({
    tenantId: z.string().min(1).max(160),
    status: runStatusSchema,
    reason: z.string().max(4000).optional(),
    externalRunId: z.string().max(500).optional(),
    data: z.record(z.string(), z.unknown()).optional(),
  })
  .strict();

const workerEventSchema = z
  .object({
    tenantId: z.string().min(1).max(160),
    type: z.literal("run.progress"),
    data: z.record(z.string(), z.unknown()),
  })
  .strict();

const workerFindingSchema = z
  .object({
    tenantId: z.string().min(1).max(160),
    finding: findingSubmissionSchema,
  })
  .strict();

const workerArtifactSchema = z
  .object({
    tenantId: z.string().min(1).max(160),
    artifact: artifactSubmissionSchema,
  })
  .strict();

export async function buildServer(dependencies: ServerDependencies): Promise<FastifyInstance> {
  const { config, store, dispatcher } = dependencies;
  const app = Fastify({
    logger: { level: config.logLevel },
    bodyLimit: 2 * 1024 * 1024,
    requestIdHeader: "x-request-id",
    genReqId: () => crypto.randomUUID(),
    trustProxy: config.environment === "production",
  });
  const authenticate = buildAuthenticator(config);
  const engineCatalog = createRuntimeEngineCatalog(config);
  const runs = new RunService(store, dispatcher, engineCatalog);
  const billing = new BillingService(config, store);
  const metrics = new Registry();
  collectDefaultMetrics({ register: metrics, prefix: "jysec_" });
  const httpRequests = new Counter({
    name: "jysec_http_requests_total",
    help: "HTTP requests processed by the JySecAI control plane",
    labelNames: ["method", "route", "status"],
    registers: [metrics],
  });

  await app.register(helmet, {
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        imgSrc: ["'self'", "data:"],
        connectSrc: ["'self'"],
      },
    },
  });
  await app.register(cors, {
    origin: config.environment === "development" ? true : new URL(config.publicBaseUrl).origin,
    credentials: true,
  });
  await app.register(rateLimit, { max: 300, timeWindow: "1 minute" });
  await app.register(rawBody, { field: "rawBody", global: false, encoding: false, runFirst: true });

  const currentDir = dirname(fileURLToPath(import.meta.url));
  await app.register(fastifyStatic, {
    root: join(currentDir, "../../public"),
    prefix: "/assets/",
  });

  app.addHook("onResponse", async (request, reply) => {
    httpRequests.inc({
      method: request.method,
      route: request.routeOptions.url ?? "unmatched",
      status: String(reply.statusCode),
    });
  });

  app.setErrorHandler((error, request, reply) => {
    if (error instanceof ZodError) {
      void reply.status(400).send({
        error: { code: "validation_error", message: "Request validation failed", issues: error.issues },
        requestId: request.id,
      });
      return;
    }
    if (error instanceof DomainError) {
      void reply.status(error.statusCode).send({
        error: { code: error.code, message: error.message, details: error.details },
        requestId: request.id,
      });
      return;
    }
    request.log.error({ err: error }, "unhandled request error");
    void reply.status(500).send({
      error: { code: "internal_error", message: "An internal error occurred" },
      requestId: request.id,
    });
  });

  app.get("/healthz", async () => ({
    status: "ok",
    product: "JySecAI",
    developer: "Jy 技術團隊",
    version: "0.1.0",
  }));

  app.get("/metrics", async (request, reply) => {
    if (!bearerTokenMatches(request, config.metricsToken)) {
      throw new DomainError("metrics_auth_denied", "Metrics authentication failed", 401);
    }
    reply.type(metrics.contentType);
    return metrics.metrics();
  });

  app.get("/", async (_request, reply) => reply.sendFile("index.html", join(currentDir, "../../public")));

  app.get("/v1/catalog", { preHandler: authenticate }, async () => ({
    product: {
      name: "JySecAI",
      developer: "Jy 技術團隊",
      architecture: "governed multi-engine security orchestration",
    },
    engines: Object.values(engineCatalog),
    plans: Object.values(planCatalog),
  }));

  app.get("/v1/usage", { preHandler: authenticate }, async (request) => {
    const actor = requireActor(request);
    const now = new Date();
    const period = `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
    const [planId, usedCredits] = await Promise.all([
      store.getTenantPlan(actor.tenantId),
      store.sumUsage(actor.tenantId, period),
    ]);
    return { period, plan: planCatalog[planId], usedCredits };
  });

  app.post("/v1/billing/checkout", { preHandler: authenticate }, async (request) => {
    const actor = requireActor(request);
    const body = z.object({ planId: planIdSchema }).strict().parse(request.body);
    return billing.createCheckout(actor, body.planId);
  });

  app.post("/v1/billing/portal", { preHandler: authenticate }, async (request) => {
    return billing.createPortal(requireActor(request));
  });

  app.get("/v1/billing/status", { preHandler: authenticate }, async (request) => {
    const actor = requireActor(request);
    return {
      enabled: billing.enabled,
      subscription: await store.getSubscription(actor.tenantId),
      selfServicePlans: ["professional", "business"],
    };
  });

  app.post(
    "/v1/billing/webhooks/stripe",
    { config: { rawBody: true } },
    async (request) => {
      const signature = String(request.headers["stripe-signature"] ?? "");
      const raw = (request as typeof request & { rawBody?: Buffer }).rawBody;
      if (!signature || !raw) {
        throw new DomainError("invalid_webhook", "Stripe signature or raw body is missing", 400);
      }
      return billing.handleWebhook(raw, signature);
    },
  );

  app.post("/v1/runs", { preHandler: authenticate }, async (request, reply) => {
    const actor = requireActor(request);
    const input = createRunSchema.parse(request.body);
    const run = await runs.create(actor, input);
    return reply.status(run.status === "awaiting_approval" ? 202 : 201).send({ run });
  });

  app.get("/v1/runs", { preHandler: authenticate }, async (request) => {
    const actor = requireActor(request);
    const query = z
      .object({
        projectId: z.string().min(1).max(160).optional(),
        limit: z.coerce.number().int().min(1).max(100).default(25),
        cursor: z.string().max(1000).optional(),
      })
      .parse(request.query);
    return store.listRuns({
      tenantId: actor.tenantId,
      limit: query.limit,
      ...(query.projectId !== undefined ? { projectId: query.projectId } : {}),
      ...(query.cursor !== undefined ? { cursor: query.cursor } : {}),
    });
  });

  app.get("/v1/runs/:runId", { preHandler: authenticate }, async (request) => {
    const actor = requireActor(request);
    const { runId } = z.object({ runId: z.string().min(1).max(200) }).parse(request.params);
    return { run: await runs.requireRun(actor.tenantId, runId) };
  });

  app.get("/v1/runs/:runId/events", { preHandler: authenticate }, async (request) => {
    const actor = requireActor(request);
    const { runId } = z.object({ runId: z.string().min(1).max(200) }).parse(request.params);
    const query = z
      .object({
        after: z.coerce.number().int().min(0).default(0),
        limit: z.coerce.number().int().min(1).max(1000).default(250),
      })
      .parse(request.query);
    await runs.requireRun(actor.tenantId, runId);
    return { events: await store.listEvents(actor.tenantId, runId, query.after, query.limit) };
  });

  app.get("/v1/runs/:runId/artifacts", { preHandler: authenticate }, async (request) => {
    const actor = requireActor(request);
    const { runId } = z.object({ runId: z.string().min(1).max(200) }).parse(request.params);
    const { limit } = z
      .object({ limit: z.coerce.number().int().min(1).max(500).default(100) })
      .parse(request.query);
    return { artifacts: await runs.listRunArtifacts(actor.tenantId, runId, limit) };
  });

  app.get("/v1/projects/:projectId/findings", { preHandler: authenticate }, async (request) => {
    const actor = requireActor(request);
    const { projectId } = z.object({ projectId: z.string().min(1).max(160) }).parse(request.params);
    const { limit } = z
      .object({ limit: z.coerce.number().int().min(1).max(500).default(100) })
      .parse(request.query);
    return { findings: await runs.listProjectFindings(actor.tenantId, projectId, limit) };
  });

  app.post("/v1/runs/:runId/approve", { preHandler: authenticate }, async (request) => {
    const actor = requireActor(request);
    const { runId } = z.object({ runId: z.string().min(1).max(200) }).parse(request.params);
    return { run: await runs.approve(actor, runId) };
  });

  app.post("/v1/runs/:runId/cancel", { preHandler: authenticate }, async (request) => {
    const actor = requireActor(request);
    const { runId } = z.object({ runId: z.string().min(1).max(200) }).parse(request.params);
    return { run: await runs.cancel(actor, runId) };
  });

  app.post("/internal/v1/runs/:runId/transition", async (request) => {
    if (!workerTokenMatches(request, config.jobSigningSecret)) {
      throw new DomainError("worker_auth_denied", "Worker authentication failed", 401);
    }
    const { runId } = z.object({ runId: z.string().min(1).max(200) }).parse(request.params);
    const transition = runTransitionSchema.parse(request.body);
    return {
      run: await runs.workerTransition({
        tenantId: transition.tenantId,
        runId,
        status: transition.status,
        ...(transition.reason !== undefined ? { reason: transition.reason } : {}),
        ...(transition.externalRunId !== undefined ? { externalRunId: transition.externalRunId } : {}),
        ...(transition.data !== undefined ? { data: transition.data } : {}),
      }),
    };
  });

  app.post("/internal/v1/runs/:runId/events", async (request, reply) => {
    if (!workerTokenMatches(request, config.jobSigningSecret)) {
      throw new DomainError("worker_auth_denied", "Worker authentication failed", 401);
    }
    const { runId } = z.object({ runId: z.string().min(1).max(200) }).parse(request.params);
    const event = workerEventSchema.parse(request.body);
    await runs.workerEvent({ tenantId: event.tenantId, runId, type: event.type, data: event.data });
    return reply.status(202).send({ accepted: true });
  });

  app.post("/internal/v1/runs/:runId/findings", async (request, reply) => {
    if (!workerTokenMatches(request, config.jobSigningSecret)) {
      throw new DomainError("worker_auth_denied", "Worker authentication failed", 401);
    }
    const { runId } = z.object({ runId: z.string().min(1).max(200) }).parse(request.params);
    const body = workerFindingSchema.parse(request.body);
    const finding = await runs.publishFinding(body.tenantId, runId, body.finding);
    return reply.status(201).send({ finding });
  });

  app.post("/internal/v1/runs/:runId/artifacts", async (request, reply) => {
    if (!workerTokenMatches(request, config.jobSigningSecret)) {
      throw new DomainError("worker_auth_denied", "Worker authentication failed", 401);
    }
    const { runId } = z.object({ runId: z.string().min(1).max(200) }).parse(request.params);
    const body = workerArtifactSchema.parse(request.body);
    const artifact = await runs.publishArtifact(body.tenantId, runId, body.artifact);
    return reply.status(201).send({ artifact });
  });

  app.addHook("onClose", async () => {
    await Promise.allSettled([store.close(), dispatcher.close()]);
  });

  app.log.info({ store: config.store }, "JySecAI control plane initialized");
  return app;
}

export function startupFailure(error: unknown): never {
  process.stderr.write(`JySecAI startup failed: ${errorMessage(error)}\n`);
  process.exit(1);
}
