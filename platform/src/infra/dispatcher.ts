import { createHmac, timingSafeEqual } from "node:crypto";

import { Redis } from "ioredis";

import type { DispatchJob, SecurityRun } from "../core/types.js";

export interface RunDispatcher {
  enqueue(run: SecurityRun): Promise<void>;
  requestCancellation(run: SecurityRun): Promise<void>;
  close(): Promise<void>;
}

function canonicalJobPayload(job: Omit<DispatchJob, "signature">): string {
  return JSON.stringify(job);
}

export function signDispatchJob(
  job: Omit<DispatchJob, "signature">,
  secret: string,
): DispatchJob {
  const signature = createHmac("sha256", secret).update(canonicalJobPayload(job)).digest("base64url");
  return { ...job, signature };
}

export function verifyDispatchJob(job: DispatchJob, secret: string): boolean {
  const { signature, ...unsigned } = job;
  const expected = createHmac("sha256", secret)
    .update(canonicalJobPayload(unsigned))
    .digest();
  let supplied: Buffer;
  try {
    supplied = Buffer.from(signature, "base64url");
  } catch {
    return false;
  }
  return supplied.length === expected.length && timingSafeEqual(supplied, expected);
}

export class RedisRunDispatcher implements RunDispatcher {
  readonly #redis: Redis;
  readonly #signingSecret: string;
  readonly #callbackBaseUrl: string;

  constructor(redisUrl: string, signingSecret: string, callbackBaseUrl: string) {
    this.#redis = new Redis(redisUrl, {
      enableReadyCheck: true,
      maxRetriesPerRequest: 3,
      lazyConnect: true,
    });
    this.#signingSecret = signingSecret;
    this.#callbackBaseUrl = callbackBaseUrl.replace(/\/$/u, "");
  }

  async enqueue(run: SecurityRun): Promise<void> {
    if (this.#redis.status === "wait") await this.#redis.connect();
    const unsigned: Omit<DispatchJob, "signature"> = {
      schemaVersion: 1,
      run,
      callbackBaseUrl: this.#callbackBaseUrl,
      issuedAt: new Date().toISOString(),
    };
    const job = signDispatchJob(unsigned, this.#signingSecret);
    await this.#redis.xadd("jysec:runs", "*", "payload", JSON.stringify(job));
  }

  async requestCancellation(run: SecurityRun): Promise<void> {
    if (this.#redis.status === "wait") await this.#redis.connect();
    await this.#redis.publish(
      "jysec:run-control",
      JSON.stringify({ action: "cancel", tenantId: run.tenantId, runId: run.id }),
    );
  }

  async close(): Promise<void> {
    if (this.#redis.status !== "end") await this.#redis.quit();
  }
}

export class MemoryRunDispatcher implements RunDispatcher {
  readonly queued: SecurityRun[] = [];
  readonly cancellations: string[] = [];

  async enqueue(run: SecurityRun): Promise<void> {
    this.queued.push(structuredClone(run));
  }

  async requestCancellation(run: SecurityRun): Promise<void> {
    this.cancellations.push(run.id);
  }

  async close(): Promise<void> {}
}
