import type { FindingSubmission, ScopeOperation } from "../core/types.js";
import type { ScannerAdapterConfig } from "./config.js";
import type { ProxyEndpoint } from "./proxy-pool.js";
import { requestJson } from "./http.js";
import {
  deduplicateFindings,
  normalizeToolFindings,
  outputExcerpt,
} from "./normalize.js";
import {
  configuredTasks,
  profileTaskLimit,
  type ScannerEngine,
  type ScannerExecutionResult,
  type ScannerJob,
  type ScannerTask,
} from "./types.js";

const webTargetTools = new Set([
  "arjun",
  "byp4xx",
  "dalfox",
  "dirb",
  "dirsearch",
  "feroxbuster",
  "ffuf",
  "gobuster",
  "httpx",
  "nikto",
  "nuclei",
  "sqlmap",
  "whatweb",
  "wpscan",
]);
const domainTargetTools = new Set(["amass", "assetfinder", "fierce", "subfinder", "subzy", "waybackurls"]);
const credentialTools = /^(hydra|john|hashcat|medusa|patator|crackmapexec|netexec)$/iu;
const validationTools = /(metasploit|msfvenom|commix|tplmap|nosqlmap|exploit|payload|shell|command|responder|pacu)/iu;
const validationArguments = /(--os-shell|--os-pwn|--dump-all|--file-write|reverse.?shell|meterpreter)/iu;
const proxyFlags: Readonly<Record<string, string>> = Object.freeze({
  arjun: "--proxy",
  dalfox: "--proxy",
  dirsearch: "--proxy",
  ffuf: "-x",
  gobuster: "--proxy",
  httpx: "-proxy",
  nuclei: "-proxy",
  sqlmap: "--proxy",
  wpscan: "--proxy",
});

function booleanConfig(config: Record<string, unknown>, key: string, fallback = false): boolean {
  return typeof config[key] === "boolean" ? Boolean(config[key]) : fallback;
}

function defaultTasks(job: ScannerJob): ScannerTask[] {
  const passive = job.run.authorization.operations.every((item) => item === "passive_discovery");
  if (passive) {
    return [
      { tool: "subfinder", parameters: {}, targetMode: "each", successMarkers: [] },
      { tool: "httpx", parameters: {}, targetMode: "each", successMarkers: [] },
    ];
  }
  const tasks: ScannerTask[] = [
    {
      tool: "nmap",
      parameters: { scan_type: "-sT -sV", additional_args: "-Pn --max-retries 2" },
      targetMode: "each",
      successMarkers: [],
    },
  ];
  if (job.run.profile !== "quick") {
    tasks.push({
      tool: "nuclei",
      parameters: { severity: "critical,high,medium" },
      targetMode: "each",
      successMarkers: [],
    });
  }
  if (job.run.profile === "deep") {
    tasks.push({ tool: "nikto", parameters: {}, targetMode: "each", successMarkers: [] });
  }
  return tasks;
}

function templateValue(value: unknown, target: string): unknown {
  if (typeof value === "string") {
    let hostname = target;
    try {
      hostname = new URL(target).hostname;
    } catch {
      hostname = target.replace(/^\[|\]$/gu, "").replace(/:\d+$/u, "");
    }
    return value
      .replaceAll("{{target}}", target)
      .replaceAll("{{url}}", target)
      .replaceAll("{{hostname}}", hostname);
  }
  if (Array.isArray(value)) return value.map((item) => templateValue(item, target));
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, item]) => [
        key,
        templateValue(item, target),
      ]),
    );
  }
  return value;
}

function taskParameters(task: ScannerTask, target: string): Record<string, unknown> {
  const rendered = templateValue(task.parameters, target) as Record<string, unknown>;
  if (Object.values(rendered).some((value) => value === target)) return rendered;
  if (webTargetTools.has(task.tool)) {
    const key = ["arjun", "byp4xx", "dalfox", "dirb", "dirsearch", "feroxbuster", "ffuf", "gobuster", "sqlmap", "wpscan"].includes(task.tool)
      ? "url"
      : "target";
    return { ...rendered, [key]: target };
  }
  if (domainTargetTools.has(task.tool)) {
    let domain = target;
    try {
      domain = new URL(target).hostname;
    } catch {
      // Host targets are already suitable.
    }
    return { ...rendered, [task.tool === "fierce" || task.tool === "assetfinder" || task.tool === "waybackurls" ? "domain" : "target"]: domain };
  }
  return { ...rendered, target };
}

function addProxy(task: ScannerTask, parameters: Record<string, unknown>, proxy?: ProxyEndpoint): Record<string, unknown> {
  const flag = proxyFlags[task.tool];
  if (!proxy || !flag) return parameters;
  const existing = typeof parameters.additional_args === "string" ? parameters.additional_args : "";
  if (/(^|\s)(-x|--proxy(?:=|\s)|-proxy(?:=|\s))/u.test(existing)) return parameters;
  return { ...parameters, additional_args: `${existing} ${flag} ${proxy.httpUrl}`.trim() };
}

function requireTaskAuthorization(
  task: ScannerTask,
  operations: ScopeOperation[],
  validationPhase: boolean,
): void {
  const serialized = JSON.stringify(task.parameters);
  const has = (operation: ScopeOperation) => operations.includes(operation);
  if (validationPhase && !has("exploit_validation")) {
    throw new Error("Validation tasks require exploit_validation authorization");
  }
  if (credentialTools.test(task.tool) && !has("credential_audit") && !has("exploit_validation")) {
    throw new Error(`Tool ${task.tool} requires credential_audit or exploit_validation authorization`);
  }
  if ((validationTools.test(task.tool) || validationArguments.test(serialized)) && !has("exploit_validation")) {
    throw new Error(`Tool ${task.tool} requires exploit_validation authorization`);
  }
  if (!has("passive_discovery") && !has("active_scan") && !has("exploit_validation") && !has("credential_audit")) {
    throw new Error("Authorization does not permit scanner operations");
  }
}

function conditionMatches(task: ScannerTask, findings: FindingSubmission[]): boolean {
  if (!task.when) return findings.length > 0;
  return findings.some((finding) => {
    const categoryMatch = !task.when?.categories?.length || task.when.categories.includes(finding.category);
    const severityMatch = !task.when?.severities?.length || task.when.severities.includes(finding.severity);
    return categoryMatch && severityMatch;
  });
}

function backendUrl(engine: Exclude<ScannerEngine, "awvs">, config: ScannerAdapterConfig): string {
  const value = engine === "hexstrike" ? config.backends.hexstrike : config.backends.kali;
  if (!value) throw new Error(`${engine} backend URL is not configured`);
  return value;
}

async function callTool(input: {
  engine: Exclude<ScannerEngine, "awvs">;
  config: ScannerAdapterConfig;
  task: ScannerTask;
  target: string;
  proxy?: ProxyEndpoint;
}): Promise<unknown> {
  if (input.task.tool === "command" && input.engine !== "kali-mcp") {
    throw new Error("Raw command tasks are only supported by kali-mcp");
  }
  const path = input.task.tool === "command"
    ? "/api/command"
    : `/api/tools/${encodeURIComponent(input.task.tool)}`;
  return requestJson(new URL(path, backendUrl(input.engine, input.config)), {
    method: "POST",
    body: addProxy(input.task, taskParameters(input.task, input.target), input.proxy),
    timeoutMs: input.config.requestTimeoutMs,
    maxResponseBytes: input.config.maxResponseBytes,
    maxRetries: input.config.maxRetries,
  });
}

interface TaskOutcome {
  tool: string;
  target: string;
  phase: "scan" | "validation";
  ok: boolean;
  output?: string;
  error?: string;
}

async function executeTasks(input: {
  engine: Exclude<ScannerEngine, "awvs">;
  config: ScannerAdapterConfig;
  job: ScannerJob;
  tasks: ScannerTask[];
  phase: "scan" | "validation";
  existingFindings: FindingSubmission[];
  proxy?: ProxyEndpoint;
}): Promise<{ findings: FindingSubmission[]; outcomes: TaskOutcome[] }> {
  const findings: FindingSubmission[] = [];
  const outcomes: TaskOutcome[] = [];
  const continueOnError = booleanConfig(input.job.run.config, "continueOnError", true);
  const engineVersion = input.engine === "hexstrike" ? "hexstrike-ai" : "mcp-kali-server";
  for (const task of input.tasks.slice(0, profileTaskLimit(input.job.run.profile))) {
    if (input.phase === "validation" && !conditionMatches(task, input.existingFindings)) continue;
    requireTaskAuthorization(task, input.job.run.authorization.operations, input.phase === "validation");
    const targets = task.targetMode === "once"
      ? [input.job.run.targets[0] as string]
      : input.job.run.targets;
    for (const target of targets) {
      try {
        const result = await callTool({
          engine: input.engine,
          config: input.config,
          task,
          target,
          ...(input.proxy ? { proxy: input.proxy } : {}),
        });
        findings.push(...normalizeToolFindings({
          engine: input.engine,
          engineVersion,
          target,
          tool: task.tool,
          result,
          task,
          validated: input.phase === "validation",
        }));
        outcomes.push({
          tool: task.tool,
          target,
          phase: input.phase,
          ok: true,
          output: outputExcerpt(result),
        });
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        outcomes.push({ tool: task.tool, target, phase: input.phase, ok: false, error: message });
        if (!continueOnError) throw error;
      }
    }
  }
  return { findings, outcomes };
}

export async function executeToolBackend(
  engine: Exclude<ScannerEngine, "awvs">,
  job: ScannerJob,
  config: ScannerAdapterConfig,
  proxy?: ProxyEndpoint,
): Promise<ScannerExecutionResult> {
  const scanTasks = configuredTasks(job.run.config, "tasks") ?? defaultTasks(job);
  const scan = await executeTasks({
    engine,
    config,
    job,
    tasks: scanTasks,
    phase: "scan",
    existingFindings: [],
    ...(proxy ? { proxy } : {}),
  });

  const autoValidate = booleanConfig(job.run.config, "autoValidate");
  const validationAuthorized = job.run.authorization.operations.includes("exploit_validation");
  const validationTasks = configuredTasks(job.run.config, "validationTasks") ?? [];
  let validation: Awaited<ReturnType<typeof executeTasks>> = { findings: [], outcomes: [] };
  if (
    autoValidate &&
    validationAuthorized &&
    scan.findings.length > 0 &&
    validationTasks.length > 0
  ) {
    validation = await executeTasks({
      engine,
      config,
      job,
      tasks: validationTasks,
      phase: "validation",
      existingFindings: scan.findings,
      ...(proxy ? { proxy } : {}),
    });
  }

  const findings = deduplicateFindings([...scan.findings, ...validation.findings]);
  const outcomes = [...scan.outcomes, ...validation.outcomes];
  return {
    externalRunId: `${engine}:${job.run.id}`,
    summary: {
      engine,
      tasksAttempted: outcomes.length,
      tasksSucceeded: outcomes.filter((item) => item.ok).length,
      tasksFailed: outcomes.filter((item) => !item.ok).length,
      findings: findings.length,
      validationRequested: autoValidate,
      validationAuthorized,
      validationTasksExecuted: validation.outcomes.length,
      outcomes,
    },
    findings,
    artifacts: [],
  };
}
