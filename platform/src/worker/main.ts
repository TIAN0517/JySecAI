import type { ChildProcess } from "node:child_process";

import { Redis } from "ioredis";

import { loadConfig } from "../config.js";
import { engineCatalog } from "../core/catalog.js";
import { errorMessage } from "../core/errors.js";
import { evaluateRunPolicy } from "../core/policy.js";
import type { DispatchJob, EngineId, RunStatus, SecurityRun } from "../core/types.js";
import { verifyDispatchJob } from "../infra/dispatcher.js";
import {
  JySecAIHttpDriver,
  type DriverCallbacks,
  type EngineDriver,
  StrixCliDriver,
  UniformHttpDriver,
} from "./drivers.js";

const group = "jysec-workers";
const stream = "jysec:runs";
const deadLetterStream = "jysec:runs:dead";

function processKey(run: Pick<SecurityRun, "tenantId" | "id">): string {
  return `${run.tenantId}:${run.id}`;
}

function adapterEnvKey(engine: EngineId): string {
  return `JYSEC_ENGINE_${engine.toUpperCase().replaceAll("-", "_")}_URL`;
}

async function callback(
  job: DispatchJob,
  path: string,
  body: Record<string, unknown>,
  secret: string,
): Promise<void> {
  const response = await fetch(new URL(path, job.callbackBaseUrl), {
    method: "POST",
    headers: { "content-type": "application/json", "x-jysec-worker-token": secret },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(15_000),
  });
  if (!response.ok) throw new Error(`Control-plane callback failed with HTTP ${response.status}`);
}

async function transition(
  job: DispatchJob,
  status: RunStatus,
  secret: string,
  options: { reason?: string; externalRunId?: string; data?: Record<string, unknown> } = {},
): Promise<void> {
  await callback(job, `/internal/v1/runs/${encodeURIComponent(job.run.id)}/transition`, {
    tenantId: job.run.tenantId,
    status,
    ...options,
  }, secret);
}

function driverFor(run: SecurityRun, config: ReturnType<typeof loadConfig>): EngineDriver {
  if (run.engine === "strix") return new StrixCliDriver(config);
  if (run.engine === "jysecai") return new JySecAIHttpDriver(config);
  const adapterUrls: Partial<Record<EngineId, string | undefined>> = config.engines.adapterUrls;
  const endpoint = adapterUrls[run.engine];
  if (!endpoint) throw new Error(`${adapterEnvKey(run.engine)} is not configured`);
  return new UniformHttpDriver(run.engine, endpoint, config.engines.adapterToken);
}

async function executeJob(
  job: DispatchJob,
  config: ReturnType<typeof loadConfig>,
  activeProcesses: Map<string, ChildProcess>,
): Promise<void> {
  if (!verifyDispatchJob(job, config.jobSigningSecret)) throw new Error("Job signature validation failed");
  const issuedAt = new Date(job.issuedAt).getTime();
  if (!Number.isFinite(issuedAt) || issuedAt > Date.now() + 5 * 60_000 || Date.now() - issuedAt > 24 * 60 * 60_000) {
    await transition(job, "failed", config.jobSigningSecret, {
      reason: "Signed dispatch job expired or failed clock validation",
    });
    return;
  }
  const policy = evaluateRunPolicy({
    tenantId: job.run.tenantId,
    projectId: job.run.projectId,
    descriptor: engineCatalog[job.run.engine],
    profile: job.run.profile,
    targets: job.run.targets,
    authorization: job.run.authorization,
  });
  if (!policy.allowed) {
    await transition(job, "failed", config.jobSigningSecret, {
      reason: `Authorization validation failed at dispatch: ${policy.reasons.join("; ")}`,
    });
    return;
  }
  await transition(job, "dispatching", config.jobSigningSecret);
  const driver = driverFor(job.run, config);
  const callbacks: DriverCallbacks = {
    registerProcess(process) {
      if (process) activeProcesses.set(processKey(job.run), process);
      else activeProcesses.delete(processKey(job.run));
    },
    async progress(data) {
      await callback(job, `/internal/v1/runs/${encodeURIComponent(job.run.id)}/events`, {
        tenantId: job.run.tenantId,
        type: "run.progress",
        data,
      }, config.jobSigningSecret);
    },
  };
  await transition(job, "running", config.jobSigningSecret);
  try {
    const result = await driver.execute(job.run, callbacks);
    for (const finding of result.findings ?? []) {
      await callback(job, `/internal/v1/runs/${encodeURIComponent(job.run.id)}/findings`, {
        tenantId: job.run.tenantId,
        finding,
      }, config.jobSigningSecret);
    }
    for (const artifact of result.artifacts ?? []) {
      await callback(job, `/internal/v1/runs/${encodeURIComponent(job.run.id)}/artifacts`, {
        tenantId: job.run.tenantId,
        artifact,
      }, config.jobSigningSecret);
    }
    await transition(job, "completed", config.jobSigningSecret, {
      ...(result.externalRunId !== undefined ? { externalRunId: result.externalRunId } : {}),
      data: result.summary,
    });
  } catch (error) {
    activeProcesses.delete(processKey(job.run));
    try {
      await transition(job, "failed", config.jobSigningSecret, { reason: errorMessage(error) });
    } catch (transitionError) {
      if (!errorMessage(transitionError).includes("HTTP 409")) throw transitionError;
    }
  }
}

async function ensureConsumerGroup(redis: Redis): Promise<void> {
  try {
    await redis.xgroup("CREATE", stream, group, "0", "MKSTREAM");
  } catch (error) {
    if (!errorMessage(error).includes("BUSYGROUP")) throw error;
  }
}

async function main(): Promise<void> {
  const config = loadConfig();
  const consumer = `worker-${process.pid}-${crypto.randomUUID().slice(0, 8)}`;
  const redis = new Redis(config.redisUrl, { maxRetriesPerRequest: null });
  const control = new Redis(config.redisUrl, { maxRetriesPerRequest: null });
  const activeProcesses = new Map<string, ChildProcess>();
  await ensureConsumerGroup(redis);
  await control.subscribe("jysec:run-control");
  control.on("message", (_channel: string, message: string) => {
    try {
      const command = JSON.parse(message) as { action?: string; tenantId?: string; runId?: string };
      if (command.action !== "cancel" || !command.tenantId || !command.runId) return;
      const child = activeProcesses.get(`${command.tenantId}:${command.runId}`);
      if (child && !child.killed) child.kill("SIGTERM");
    } catch {
      // Invalid control messages are ignored; the private control channel is not a trust boundary.
    }
  });

  let stopping = false;
  const stop = () => {
    stopping = true;
    for (const child of activeProcesses.values()) if (!child.killed) child.kill("SIGTERM");
  };
  process.once("SIGINT", stop);
  process.once("SIGTERM", stop);

  while (!stopping) {
    const batches = await redis.xreadgroup(
      "GROUP",
      group,
      consumer,
      "COUNT",
      1,
      "BLOCK",
      5_000,
      "STREAMS",
      stream,
      ">",
    );
    if (!batches) continue;
    for (const [, messages] of batches as [string, [string, string[]][]][]) {
      for (const [messageId, fields] of messages) {
        const payloadIndex = fields.indexOf("payload");
        try {
          const payload = payloadIndex < 0 ? undefined : fields[payloadIndex + 1];
          if (!payload) throw new Error("Queue message has no payload");
          const job = JSON.parse(payload) as DispatchJob;
          await executeJob(job, config, activeProcesses);
          await redis.xack(stream, group, messageId);
        } catch (error) {
          process.stderr.write(`JySecAI worker job ${messageId} failed: ${errorMessage(error)}\n`);
          const payload = payloadIndex < 0 ? "" : (fields[payloadIndex + 1] ?? "");
          await redis.xadd(
            deadLetterStream,
            "MAXLEN",
            "~",
            "10000",
            "*",
            "sourceMessageId",
            messageId,
            "failedAt",
            new Date().toISOString(),
            "error",
            errorMessage(error).slice(0, 4000),
            "payload",
            payload,
          );
          await redis.xack(stream, group, messageId);
        }
      }
    }
  }
  await Promise.allSettled([redis.quit(), control.quit()]);
}

main().catch((error) => {
  process.stderr.write(`JySecAI worker failed: ${errorMessage(error)}\n`);
  process.exit(1);
});
