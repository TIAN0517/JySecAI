import { createHash } from "node:crypto";

import type { FindingSubmission } from "../core/types.js";
import type { ScannerEngine, ScannerTask } from "./types.js";

type JsonRecord = Record<string, unknown>;

function record(value: unknown): JsonRecord | undefined {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as JsonRecord)
    : undefined;
}

function text(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function severity(value: unknown): FindingSubmission["severity"] {
  if (typeof value === "number") {
    if (value >= 9) return "critical";
    if (value >= 7) return "high";
    if (value >= 4) return "medium";
    if (value > 0) return "low";
    return "info";
  }
  const normalized = String(value ?? "").toLowerCase();
  if (normalized.includes("critical")) return "critical";
  if (normalized.includes("high")) return "high";
  if (normalized.includes("medium") || normalized.includes("moderate")) return "medium";
  if (normalized.includes("low")) return "low";
  return "info";
}

export function findingFingerprint(
  engine: ScannerEngine,
  target: string,
  category: string,
  title: string,
): string {
  return createHash("sha256")
    .update([engine, target, category, title].join("\u0000"))
    .digest("hex");
}

function candidateObjects(value: unknown, depth = 0, output: JsonRecord[] = []): JsonRecord[] {
  if (depth > 6 || output.length >= 500) return output;
  if (Array.isArray(value)) {
    for (const item of value) candidateObjects(item, depth + 1, output);
    return output;
  }
  const object = record(value);
  if (!object) return output;
  const title = text(object.title) ?? text(object.name) ?? text(object.vulnerability);
  const hasRiskSignal =
    object.severity !== undefined ||
    object.risk !== undefined ||
    object.cvss_score !== undefined ||
    object.vuln_id !== undefined ||
    object.vt_id !== undefined;
  if (title && hasRiskSignal) output.push(object);
  for (const [key, child] of Object.entries(object)) {
    if (["vulnerabilities", "findings", "issues", "results", "data"].includes(key.toLowerCase())) {
      candidateObjects(child, depth + 1, output);
    }
  }
  return output;
}

function jsonLines(value: unknown): unknown[] {
  if (typeof value !== "string") return [];
  const parsed: unknown[] = [];
  for (const line of value.split(/\r?\n/u).slice(0, 2000)) {
    if (!line.trim().startsWith("{")) continue;
    try {
      parsed.push(JSON.parse(line) as unknown);
    } catch {
      // Tool output commonly mixes log lines with JSONL.
    }
  }
  return parsed;
}

function confidence(object: JsonRecord, validated: boolean): number {
  const raw = Number(object.confidence);
  if (Number.isFinite(raw)) return Math.max(0, Math.min(1, raw > 1 ? raw / 100 : raw));
  return validated ? 0.95 : 0.75;
}

export function outputExcerpt(value: unknown, maximum = 3000): string {
  let rendered: string;
  try {
    rendered = typeof value === "string" ? value : JSON.stringify(value);
  } catch {
    rendered = String(value);
  }
  return rendered.length <= maximum ? rendered : `${rendered.slice(0, maximum)}…`;
}

export function normalizeToolFindings(input: {
  engine: ScannerEngine;
  engineVersion: string;
  target: string;
  tool: string;
  result: unknown;
  task: ScannerTask;
  validated: boolean;
}): FindingSubmission[] {
  const candidates = candidateObjects(input.result);
  const response = record(input.result);
  for (const parsed of jsonLines(response?.output ?? response?.data)) {
    candidateObjects(parsed, 0, candidates);
  }
  const findings = candidates.map((item, index): FindingSubmission => {
    const title = text(item.title) ?? text(item.name) ?? text(item.vulnerability) ?? `${input.tool} finding`;
    const category = text(item.category) ?? text(item.type) ?? input.tool;
    const remediation = text(item.remediation) ?? text(item.recommendation);
    const reproduction = text(item.reproduction) ?? text(item.description) ?? text(item.details);
    return {
      engineVersion: input.engineVersion,
      testCaseId: text(item.vuln_id) ?? text(item.vt_id) ?? `${input.tool}-${index + 1}`,
      category,
      title,
      severity: severity(item.severity ?? item.risk ?? item.cvss_score),
      confidence: confidence(item, input.validated),
      status: input.validated ? "confirmed" : "suspected",
      evidenceRefs: [`${input.engine}:${input.tool}:${input.target}`],
      ...(reproduction ? { reproductionSummary: reproduction.slice(0, 12_000) } : {}),
      ...(remediation ? { remediation: remediation.slice(0, 12_000) } : {}),
      fingerprint: findingFingerprint(input.engine, input.target, category, title),
    };
  });

  const rendered = outputExcerpt(input.result, 100_000).toLowerCase();
  const markerMatched = input.task.successMarkers.some((marker) =>
    rendered.includes(marker.toLowerCase()),
  );
  if (input.task.finding && markerMatched) {
    const hint = input.task.finding;
    findings.push({
      engineVersion: input.engineVersion,
      category: hint.category,
      title: hint.title,
      severity: hint.severity,
      confidence: input.validated ? 0.98 : 0.85,
      status: input.validated ? "confirmed" : "suspected",
      evidenceRefs: [`${input.engine}:${input.tool}:${input.target}`],
      reproductionSummary: `Configured success marker observed in ${input.tool} output.`,
      ...(hint.remediation ? { remediation: hint.remediation } : {}),
      fingerprint: findingFingerprint(input.engine, input.target, hint.category, hint.title),
    });
  }
  return findings;
}

export function deduplicateFindings(findings: FindingSubmission[]): FindingSubmission[] {
  const unique = new Map<string, FindingSubmission>();
  for (const finding of findings) {
    const key = finding.fingerprint ?? `${finding.category}:${finding.title}`;
    const current = unique.get(key);
    if (!current || finding.confidence > current.confidence) unique.set(key, finding);
  }
  return [...unique.values()].slice(0, 500);
}
