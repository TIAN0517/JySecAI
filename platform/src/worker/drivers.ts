import { spawn, type ChildProcess } from "node:child_process";
import { mkdir, readdir, stat, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { createInterface } from "node:readline";
import { z } from "zod";

import type { AppConfig } from "../config.js";
import { DomainError, errorMessage } from "../core/errors.js";
import {
  artifactSubmissionSchema,
  findingSubmissionSchema,
  type ArtifactSubmission,
  type EngineId,
  type FindingSubmission,
  type SecurityRun,
} from "../core/types.js";

export interface DriverCallbacks {
  progress(data: Record<string, unknown>): Promise<void>;
  registerProcess(process: ChildProcess | null): void;
}

export interface EngineResult {
  externalRunId?: string;
  summary: Record<string, unknown>;
  findings?: FindingSubmission[];
  artifacts?: ArtifactSubmission[];
}

const adapterResultSchema = z
  .object({
    externalRunId: z.string().min(1).max(500).optional(),
    summary: z.record(z.string(), z.unknown()).default({}),
    findings: z.array(findingSubmissionSchema).max(500).default([]),
    artifacts: z.array(artifactSubmissionSchema).max(500).default([]),
  })
  .strict();

export interface EngineDriver {
  readonly id: EngineId;
  execute(run: SecurityRun, callbacks: DriverCallbacks): Promise<EngineResult>;
}

const profileTimeoutMs: Record<SecurityRun["profile"], number> = {
  audit: 30 * 60_000,
  quick: 60 * 60_000,
  standard: 4 * 60 * 60_000,
  deep: 12 * 60 * 60_000,
};

const profileBudgetUsd: Record<SecurityRun["profile"], number> = {
  audit: 2,
  quick: 5,
  standard: 15,
  deep: 40,
};

function requestedBudget(run: SecurityRun): number {
  const requested = Number(run.config.maxBudgetUsd);
  const ceiling = profileBudgetUsd[run.profile];
  return Number.isFinite(requested) && requested > 0 ? Math.min(requested, ceiling) : ceiling;
}

function requestedMaxTurns(run: SecurityRun): number {
  const requested = Number(run.config.maxTurns);
  return Number.isInteger(requested) && requested >= 10 ? Math.min(requested, 500) : 100;
}

async function newestDirectory(root: string): Promise<string | undefined> {
  let entries;
  try {
    entries = await readdir(root, { withFileTypes: true });
  } catch {
    return undefined;
  }
  const candidates = await Promise.all(
    entries
      .filter((entry) => entry.isDirectory())
      .map(async (entry) => ({ name: entry.name, mtime: (await stat(join(root, entry.name))).mtimeMs })),
  );
  return candidates.sort((left, right) => right.mtime - left.mtime)[0]?.name;
}

export class StrixCliDriver implements EngineDriver {
  readonly id = "strix" as const;
  readonly #config: AppConfig;

  constructor(config: AppConfig) {
    this.#config = config;
  }

  async execute(run: SecurityRun, callbacks: DriverCallbacks): Promise<EngineResult> {
    if (run.profile === "audit") throw new DomainError("invalid_profile", "Strix does not support audit profile");
    const runRoot = resolve(this.#config.runsRoot, run.tenantId, run.id);
    await mkdir(runRoot, { recursive: true, mode: 0o700 });
    const instructionPath = join(runRoot, "authorized-objective.md");
    const instruction = [
      "# Immutable authorization boundary",
      `Authorization ID: ${run.authorization.id}`,
      `Authorized targets: ${run.targets.join(", ")}`,
      `Permitted operations: ${run.authorization.operations.join(", ")}`,
      "Do not test, pivot to, or interact with any target outside this list.",
      "Stop and report an authorization conflict instead of widening scope.",
      "",
      "# Engagement objective",
      run.objective,
    ].join("\n");
    await writeFile(instructionPath, instruction, { encoding: "utf8", mode: 0o600, flag: "wx" });

    const args = ["-n", "--scan-mode", run.profile, "--max-budget", String(requestedBudget(run))];
    args.push("--max-turns", String(requestedMaxTurns(run)), "--instruction-file", instructionPath);
    for (const target of run.targets) args.push("--target", target);

    const environment: NodeJS.ProcessEnv = {
      PATH: process.env.PATH,
      HOME: process.env.HOME,
      LANG: process.env.LANG ?? "C.UTF-8",
      NO_COLOR: "1",
      STRIX_TELEMETRY_DISABLED: "1",
    };
    if (this.#config.engines.strixLlm) environment.STRIX_LLM = this.#config.engines.strixLlm;
    if (this.#config.engines.llmApiKey) environment.LLM_API_KEY = this.#config.engines.llmApiKey;

    const child = spawn(this.#config.engines.strixBin, args, {
      cwd: runRoot,
      env: environment,
      shell: false,
      detached: false,
      stdio: ["ignore", "pipe", "pipe"],
    });
    callbacks.registerProcess(child);
    const timeout = setTimeout(() => child.kill("SIGTERM"), profileTimeoutMs[run.profile]);
    timeout.unref();

    let lineCount = 0;
    let lastProgressAt = 0;
    const relay = async (stream: NodeJS.ReadableStream, channel: "stdout" | "stderr") => {
      const lines = createInterface({ input: stream });
      for await (const raw of lines) {
        lineCount += 1;
        const now = Date.now();
        if (now - lastProgressAt < 750 && channel === "stdout") continue;
        lastProgressAt = now;
        await callbacks.progress({ channel, line: String(raw).slice(0, 4000), lineCount });
      }
    };
    const outputRelay = Promise.all([relay(child.stdout, "stdout"), relay(child.stderr, "stderr")]);
    const exitCode = await new Promise<number>((resolveExit, reject) => {
      child.once("error", reject);
      child.once("exit", (code, signal) => {
        if (signal) reject(new Error(`Strix terminated by signal ${signal}`));
        else resolveExit(code ?? 1);
      });
    }).finally(() => clearTimeout(timeout));
    await outputRelay;
    callbacks.registerProcess(null);

    const externalRunId = await newestDirectory(join(runRoot, "strix_runs"));
    if (exitCode !== 0 && exitCode !== 2) {
      throw new Error(`Strix exited with code ${exitCode}`);
    }
    return {
      ...(externalRunId !== undefined ? { externalRunId } : {}),
      summary: {
        exitCode,
        findingsPresent: exitCode === 2,
        outputLines: lineCount,
        artifactsRoot: externalRunId ? join(runRoot, "strix_runs", externalRunId) : runRoot,
      },
    };
  }
}

export class JySecAIHttpDriver implements EngineDriver {
  readonly id = "jysecai" as const;
  readonly #config: AppConfig;

  constructor(config: AppConfig) {
    this.#config = config;
  }

  async execute(run: SecurityRun, callbacks: DriverCallbacks): Promise<EngineResult> {
    const token = this.#config.engines.jysecaiServiceToken;
    if (!token) throw new Error("JYSECAI_SERVICE_TOKEN is not configured");
    callbacks.registerProcess(null);
    const message = [
      `Authorization ID: ${run.authorization.id}`,
      `Authorized targets only: ${run.targets.join(", ")}`,
      `Permitted operations: ${run.authorization.operations.join(", ")}`,
      "Never widen scope. Stop if the objective conflicts with this boundary.",
      "",
      run.objective,
    ].join("\n");
    const orchestration = String(run.config.orchestration ?? "supervisor");
    const endpoint = orchestration === "single" ? "/api/eino-agent" : "/api/multi-agent";
    await callbacks.progress({ phase: "jysecai.request", orchestration });
    const response = await fetch(new URL(endpoint, this.#config.engines.jysecaiBaseUrl), {
      method: "POST",
      headers: {
        authorization: `Bearer ${token}`,
        "content-type": "application/json",
        "x-jysec-run-id": run.id,
      },
      body: JSON.stringify({
        message,
        projectId: run.projectId,
        ...(endpoint.endsWith("multi-agent") ? { orchestration } : {}),
        hitl: { enabled: true, mode: "block", reviewer: "human" },
        finalization: { requireExecutionEvidence: true },
      }),
      signal: AbortSignal.timeout(profileTimeoutMs[run.profile]),
    });
    const text = await response.text();
    if (!response.ok) throw new Error(`JySecAI returned HTTP ${response.status}: ${text.slice(0, 1000)}`);
    let result: Record<string, unknown>;
    try {
      result = JSON.parse(text) as Record<string, unknown>;
    } catch {
      throw new Error("JySecAI returned a non-JSON response");
    }
    await callbacks.progress({
      phase: "jysecai.response",
      finalized: result.finalized,
      evidenceVerified: result.evidenceVerified,
    });
    return {
      ...(typeof result.conversationId === "string" ? { externalRunId: result.conversationId } : {}),
      summary: {
        status: result.status,
        finalized: result.finalized,
        finalizable: result.finalizable,
        evidenceVerified: result.evidenceVerified,
        evidenceRefs: result.evidenceRefs,
      },
    };
  }
}

export class UniformHttpDriver implements EngineDriver {
  readonly id: EngineId;
  readonly #endpoint: URL;
  readonly #token: string | undefined;

  constructor(id: EngineId, endpoint: string, token?: string) {
    this.id = id;
    this.#endpoint = new URL("/v1/jobs/execute", endpoint);
    this.#token = token;
  }

  async execute(run: SecurityRun, callbacks: DriverCallbacks): Promise<EngineResult> {
    callbacks.registerProcess(null);
    await callbacks.progress({ phase: `${this.id}.request` });
    const response = await fetch(this.#endpoint, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(this.#token ? { authorization: `Bearer ${this.#token}` } : {}),
      },
      body: JSON.stringify({ schemaVersion: 1, run }),
      signal: AbortSignal.timeout(profileTimeoutMs[run.profile]),
    });
    const text = await response.text();
    if (!response.ok) throw new Error(`${this.id} adapter returned HTTP ${response.status}: ${text.slice(0, 1000)}`);
    try {
      const parsed = adapterResultSchema.parse(JSON.parse(text));
      return {
        ...(parsed.externalRunId !== undefined ? { externalRunId: parsed.externalRunId } : {}),
        summary: parsed.summary,
        findings: parsed.findings,
        artifacts: parsed.artifacts,
      };
    } catch (error) {
      throw new Error(`${this.id} adapter returned invalid JSON: ${errorMessage(error)}`);
    }
  }
}
