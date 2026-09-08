import { readFile } from "node:fs/promises";

import type { FindingSubmission } from "../core/types.js";
import type { ScannerAdapterConfig } from "./config.js";
import { requestJson, requestJsonResponse, type JsonRequestOptions } from "./http.js";
import { deduplicateFindings, findingFingerprint } from "./normalize.js";
import type { ScannerExecutionResult, ScannerJob } from "./types.js";
import type { ProxyEndpoint } from "./proxy-pool.js";

type JsonRecord = Record<string, unknown>;

const fullScanProfile = "11111111-1111-1111-1111-111111111111";
const highRiskProfile = "11111111-1111-1111-1111-111111111112";
const terminalStatuses = new Set(["aborted", "completed", "failed"]);

function record(value: unknown): JsonRecord | undefined {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as JsonRecord
    : undefined;
}

function records(value: unknown): JsonRecord[] {
  return Array.isArray(value) ? value.map(record).filter((item): item is JsonRecord => Boolean(item)) : [];
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function numberConfig(config: JsonRecord, key: string, fallback: number, maximum: number): number {
  const parsed = Number(config[key]);
  return Number.isFinite(parsed) && parsed > 0
    ? Math.min(maximum, Math.floor(parsed))
    : fallback;
}

function booleanConfig(config: JsonRecord, key: string): boolean {
  return config[key] === true;
}

function apiBase(config: ScannerAdapterConfig): URL {
  if (!config.backends.awvs) throw new Error("AWVS backend URL is not configured");
  const base = new URL(config.backends.awvs);
  const trimmed = base.pathname.replace(/\/+$/u, "");
  base.pathname = trimmed.endsWith("/api/v1") ? `${trimmed}/` : "/api/v1/";
  base.search = "";
  base.hash = "";
  return base;
}

function apiUrl(config: ScannerAdapterConfig, path: string): URL {
  return new URL(path.replace(/^\//u, ""), apiBase(config));
}

async function caCertificate(config: ScannerAdapterConfig): Promise<Buffer | undefined> {
  return config.backends.awvsCaFile ? readFile(config.backends.awvsCaFile) : undefined;
}

function options(
  config: ScannerAdapterConfig,
  apiKey: string,
  ca: Buffer | undefined,
  method: "GET" | "POST" | "PUT" | "PATCH",
  body?: unknown,
): JsonRequestOptions {
  return {
    method,
    headers: { "X-Auth": apiKey },
    ...(body === undefined ? {} : { body }),
    timeoutMs: config.requestTimeoutMs,
    maxResponseBytes: config.maxResponseBytes,
    maxRetries: config.maxRetries,
    ...(ca ? { ca } : {}),
    ...(config.backends.awvsTlsServerName
      ? { tlsServerName: config.backends.awvsTlsServerName }
      : {}),
  };
}

function identifier(value: unknown, key: string, location?: string): string | undefined {
  const direct = stringValue(record(value)?.[key]);
  if (direct) return direct;
  if (!location) return undefined;
  const parts = location.split("/").filter(Boolean);
  return parts.at(-1);
}

function normalizeAddress(value: string): string {
  return value.trim().replace(/\/+$/u, "").toLowerCase();
}

async function targetId(input: {
  config: ScannerAdapterConfig;
  apiKey: string;
  ca?: Buffer;
  target: string;
  job: ScannerJob;
}): Promise<string> {
  const query = apiUrl(input.config, "targets");
  query.searchParams.set("q", input.target);
  query.searchParams.set("l", "100");
  const listed = record(await requestJson(query, options(input.config, input.apiKey, input.ca, "GET")));
  const target = records(listed?.targets).find((item) => {
    const address = stringValue(item.address);
    return address !== undefined && normalizeAddress(address) === normalizeAddress(input.target);
  });
  const existingId = stringValue(target?.target_id);
  if (existingId) return existingId;

  const created = await requestJsonResponse(
    apiUrl(input.config, "targets"),
    options(input.config, input.apiKey, input.ca, "POST", {
      address: input.target,
      description: `JySecAI ${input.job.run.projectId} / ${input.job.run.id}`.slice(0, 1024),
      criticality: 10,
    }),
  );
  const createdId = identifier(created.body, "target_id", stringValue(created.headers.location));
  if (!createdId) throw new Error("AWVS did not return a target identifier");
  return createdId;
}

async function configureTargetProxy(input: {
  config: ScannerAdapterConfig;
  apiKey: string;
  ca?: Buffer;
  targetId: string;
  proxy?: ProxyEndpoint;
}): Promise<void> {
  if (!input.proxy) return;
  await requestJsonResponse(
    apiUrl(input.config, `targets/${encodeURIComponent(input.targetId)}/configuration`),
    options(input.config, input.apiKey, input.ca, "PATCH", {
      proxy: {
        protocol: "http",
        address: new URL(input.proxy.httpUrl).hostname,
        port: Number(new URL(input.proxy.httpUrl).port),
        enabled: true,
      },
    }),
  );
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function profileId(job: ScannerJob): string {
  const configured = stringValue(job.run.config.scanProfileId);
  if (configured) return configured;
  return job.run.profile === "quick" ? highRiskProfile : fullScanProfile;
}

async function scheduleScan(input: {
  config: ScannerAdapterConfig;
  apiKey: string;
  ca?: Buffer;
  targetId: string;
  job: ScannerJob;
}): Promise<string> {
  const response = await requestJsonResponse(
    apiUrl(input.config, "scans"),
    options(input.config, input.apiKey, input.ca, "POST", {
      target_id: input.targetId,
      profile_id: profileId(input.job),
      schedule: { disable: false, start_date: null, time_sensitive: false },
    }),
  );
  const scanId = identifier(response.body, "scan_id", stringValue(response.headers.location));
  if (!scanId) throw new Error("AWVS did not return a scan identifier");
  return scanId;
}

interface CompletedScan {
  scanId: string;
  sessionId?: string;
  progress: number;
}

async function waitForScan(input: {
  config: ScannerAdapterConfig;
  apiKey: string;
  ca?: Buffer;
  scanId: string;
  maxMinutes: number;
}): Promise<CompletedScan> {
  const deadline = Date.now() + input.maxMinutes * 60_000;
  let lastStatus = "scheduled";
  let progress = 0;
  while (Date.now() < deadline) {
    const response = record(await requestJson(
      apiUrl(input.config, `scans/${encodeURIComponent(input.scanId)}`),
      options(input.config, input.apiKey, input.ca, "GET"),
    ));
    const current = record(response?.current_session);
    lastStatus = String(current?.status ?? response?.status ?? "scheduled").toLowerCase();
    progress = Number(current?.progress ?? response?.progress ?? 0);
    if (terminalStatuses.has(lastStatus)) {
      if (lastStatus !== "completed") throw new Error(`AWVS scan ${input.scanId} ended as ${lastStatus}`);
      const sessionId = stringValue(current?.scan_session_id);
      return {
        scanId: input.scanId,
        ...(sessionId ? { sessionId } : {}),
        progress,
      };
    }
    await delay(input.config.awvsPollIntervalMs);
  }
  throw new Error(`AWVS scan ${input.scanId} timed out after ${input.maxMinutes} minutes (${lastStatus})`);
}

async function resultId(input: {
  config: ScannerAdapterConfig;
  apiKey: string;
  ca?: Buffer;
  scan: CompletedScan;
}): Promise<string> {
  const url = apiUrl(input.config, `scans/${encodeURIComponent(input.scan.scanId)}/results`);
  url.searchParams.set("l", "100");
  url.searchParams.set("s", "-start_date");
  const response = record(await requestJson(url, options(input.config, input.apiKey, input.ca, "GET")));
  const completed = records(response?.results).find((item) =>
    String(item.status ?? "").toLowerCase() === "completed"
  ) ?? records(response?.results)[0];
  const value = stringValue(completed?.result_id) ?? input.scan.sessionId;
  if (!value) throw new Error(`AWVS scan ${input.scan.scanId} did not return a result identifier`);
  return value;
}

async function vulnerabilities(input: {
  config: ScannerAdapterConfig;
  apiKey: string;
  ca?: Buffer;
  scanId: string;
  resultId: string;
}): Promise<JsonRecord[]> {
  const output: JsonRecord[] = [];
  const seenCursors = new Set<string>();
  let cursor: string | undefined;
  for (let page = 0; page < 10 && output.length < 500; page += 1) {
    const url = apiUrl(
      input.config,
      `scans/${encodeURIComponent(input.scanId)}/results/${encodeURIComponent(input.resultId)}/vulnerabilities`,
    );
    url.searchParams.set("l", "100");
    if (cursor) url.searchParams.set("c", cursor);
    const response = record(await requestJson(url, options(input.config, input.apiKey, input.ca, "GET")));
    const pageItems = records(response?.vulnerabilities);
    output.push(...pageItems);
    if (pageItems.length < 100) break;
    const cursors = Array.isArray(record(response?.pagination)?.cursors)
      ? record(response?.pagination)?.cursors as unknown[]
      : [];
    const next = cursors.map(stringValue).find((item): item is string =>
      Boolean(item) && item !== cursor && !seenCursors.has(item as string)
    );
    if (!next) break;
    seenCursors.add(next);
    cursor = next;
  }
  return output.slice(0, 500);
}

function awvsSeverity(value: unknown): FindingSubmission["severity"] {
  const number = Number(value);
  if (number >= 4) return "critical";
  if (number >= 3) return "high";
  if (number >= 2) return "medium";
  if (number >= 1) return "low";
  return "info";
}

function normalizeVulnerability(
  item: JsonRecord,
  target: string,
  scanId: string,
  resultIdValue: string,
  validated: boolean,
): FindingSubmission {
  const title = stringValue(item.vt_name) ?? "Acunetix finding";
  const category = records(item.tags).map((tag) => stringValue(tag.name)).find(Boolean)
    ?? stringValue(item.source)
    ?? "web-vulnerability";
  const affected = [stringValue(item.affects_url), stringValue(item.affects_detail)]
    .filter((value): value is string => Boolean(value))
    .join(" — ");
  const rawConfidence = Number(item.confidence);
  const confidence = Number.isFinite(rawConfidence)
    ? Math.max(0, Math.min(1, rawConfidence > 1 ? rawConfidence / 100 : rawConfidence))
    : validated ? 0.98 : 0.9;
  const vulnId = stringValue(item.vuln_id) ?? stringValue(item.target_vuln_id);
  return {
    engineVersion: "acunetix-25",
    ...(stringValue(item.vt_id) || vulnId ? { testCaseId: stringValue(item.vt_id) ?? vulnId } : {}),
    category,
    title,
    severity: awvsSeverity(item.severity),
    confidence,
    status: validated ? "confirmed" : "suspected",
    evidenceRefs: [`awvs:${scanId}:${resultIdValue}:${vulnId ?? "finding"}`],
    ...(affected ? { reproductionSummary: affected.slice(0, 12_000) } : {}),
    fingerprint: findingFingerprint("awvs", target, category, title),
  };
}

interface ValidationResult {
  scheduled: number;
  completed: number;
  findings: FindingSubmission[];
  errors: string[];
}

async function recheckVulnerabilities(input: {
  config: ScannerAdapterConfig;
  apiKey: string;
  ca?: Buffer;
  job: ScannerJob;
  target: string;
  scanId: string;
  resultId: string;
  vulnerabilities: JsonRecord[];
  maxMinutes: number;
}): Promise<ValidationResult> {
  const maximum = numberConfig(input.job.run.config, "maxValidationFindings", 10, 25);
  const scanIds = new Set<string>();
  const errors: string[] = [];
  let scheduled = 0;
  for (const item of input.vulnerabilities.slice(0, maximum)) {
    const vulnId = stringValue(item.vuln_id) ?? stringValue(item.target_vuln_id);
    if (!vulnId) continue;
    try {
      const response = await requestJsonResponse(
        apiUrl(
          input.config,
          `scans/${encodeURIComponent(input.scanId)}/results/${encodeURIComponent(input.resultId)}/vulnerabilities/${encodeURIComponent(vulnId)}/recheck`,
        ),
        options(input.config, input.apiKey, input.ca, "PUT", {}),
      );
      scheduled += 1;
      const scanIdValue = identifier(
        response.body,
        "scan_id",
        stringValue(response.headers.location),
      );
      if (scanIdValue) scanIds.add(scanIdValue);
    } catch (error) {
      errors.push(error instanceof Error ? error.message : String(error));
    }
  }

  const findings: FindingSubmission[] = [];
  let completed = 0;
  for (const scanIdValue of scanIds) {
    try {
      const scan = await waitForScan({
        config: input.config,
        apiKey: input.apiKey,
        ...(input.ca ? { ca: input.ca } : {}),
        scanId: scanIdValue,
        maxMinutes: input.maxMinutes,
      });
      const resultIdValue = await resultId({
        config: input.config,
        apiKey: input.apiKey,
        ...(input.ca ? { ca: input.ca } : {}),
        scan,
      });
      const verified = await vulnerabilities({
        config: input.config,
        apiKey: input.apiKey,
        ...(input.ca ? { ca: input.ca } : {}),
        scanId: scanIdValue,
        resultId: resultIdValue,
      });
      findings.push(...verified.map((item) =>
        normalizeVulnerability(item, input.target, scanIdValue, resultIdValue, true)
      ));
      completed += 1;
    } catch (error) {
      errors.push(error instanceof Error ? error.message : String(error));
    }
  }
  return { scheduled, completed, findings, errors };
}

export async function executeAwvs(
  job: ScannerJob,
  config: ScannerAdapterConfig,
  proxy?: ProxyEndpoint,
): Promise<ScannerExecutionResult> {
  const apiKey = config.backends.awvsApiKey;
  if (!apiKey) throw new Error("JYSEC_AWVS_API_KEY is not configured");
  const ca = await caCertificate(config);
  const profileMinutes = { audit: 30, quick: 60, standard: 240, deep: 720 }[job.run.profile];
  const maxMinutes = numberConfig(job.run.config, "maxScanMinutes", profileMinutes, 1_440);
  const autoValidate = booleanConfig(job.run.config, "autoValidate");
  const validationAuthorized = job.run.authorization.operations.includes("exploit_validation");
  const continueOnError = job.run.config.continueOnError !== false;
  const findings: FindingSubmission[] = [];
  const runs: JsonRecord[] = [];

  for (const target of job.run.targets) {
    try {
      const id = await targetId({
        config,
        apiKey,
        ...(ca ? { ca } : {}),
        target,
        job,
      });
      await configureTargetProxy({
        config,
        apiKey,
        ...(ca ? { ca } : {}),
        targetId: id,
        ...(proxy ? { proxy } : {}),
      });
      const scanIdValue = await scheduleScan({
        config,
        apiKey,
        ...(ca ? { ca } : {}),
        targetId: id,
        job,
      });
      const scan = await waitForScan({
        config,
        apiKey,
        ...(ca ? { ca } : {}),
        scanId: scanIdValue,
        maxMinutes,
      });
      const resultIdValue = await resultId({
        config,
        apiKey,
        ...(ca ? { ca } : {}),
        scan,
      });
      const rawFindings = await vulnerabilities({
        config,
        apiKey,
        ...(ca ? { ca } : {}),
        scanId: scanIdValue,
        resultId: resultIdValue,
      });
      findings.push(...rawFindings.map((item) =>
        normalizeVulnerability(item, target, scanIdValue, resultIdValue, false)
      ));

      const validation = autoValidate && validationAuthorized && rawFindings.length > 0
        ? await recheckVulnerabilities({
            config,
            apiKey,
            ...(ca ? { ca } : {}),
            job,
            target,
            scanId: scanIdValue,
            resultId: resultIdValue,
            vulnerabilities: rawFindings,
            maxMinutes: numberConfig(job.run.config, "maxValidationMinutes", 120, 720),
          })
        : { scheduled: 0, completed: 0, findings: [], errors: [] };
      findings.push(...validation.findings);
      runs.push({
        target,
        targetId: id,
        scanId: scanIdValue,
        resultId: resultIdValue,
        progress: scan.progress,
        vulnerabilities: rawFindings.length,
        validationScheduled: validation.scheduled,
        validationCompleted: validation.completed,
        validationErrors: validation.errors,
      });
    } catch (error) {
      runs.push({
        target,
        error: error instanceof Error ? error.message : String(error),
      });
      if (!continueOnError) throw error;
    }
  }

  const normalized = deduplicateFindings(findings);
  const successful = runs.filter((item) => item.error === undefined).length;
  if (successful === 0) throw new Error(`All AWVS scans failed: ${JSON.stringify(runs)}`);
  const externalRunId = stringValue(runs.find((item) => item.scanId)?.scanId);
  return {
    ...(externalRunId ? { externalRunId } : {}),
    summary: {
      engine: "awvs",
      scansSucceeded: successful,
      scansFailed: runs.length - successful,
      findings: normalized.length,
      validationRequested: autoValidate,
      validationAuthorized,
      runs,
    },
    findings: normalized,
    artifacts: [],
  };
}
