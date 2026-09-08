import { z } from "zod";

import { scopeOperationSchema, type FindingSubmission, type RunProfile } from "../core/types.js";

export const scannerEngineSchema = z.enum(["hexstrike", "kali-mcp", "awvs"]);
export type ScannerEngine = z.infer<typeof scannerEngineSchema>;

const findingHintSchema = z
  .object({
    category: z.string().min(1).max(320),
    title: z.string().min(1).max(1000),
    severity: z.enum(["critical", "high", "medium", "low", "info"]),
    remediation: z.string().max(12_000).optional(),
  })
  .strict();

const taskConditionSchema = z
  .object({
    categories: z.array(z.string().min(1).max(320)).max(50).optional(),
    severities: z.array(z.enum(["critical", "high", "medium", "low", "info"])).max(5).optional(),
  })
  .strict();

export const scannerTaskSchema = z
  .object({
    tool: z.string().min(1).max(100).regex(/^[a-zA-Z0-9][a-zA-Z0-9._-]*$/u),
    parameters: z.record(z.string(), z.unknown()).default({}),
    targetMode: z.enum(["each", "once"]).default("each"),
    successMarkers: z.array(z.string().min(1).max(500)).max(30).default([]),
    finding: findingHintSchema.optional(),
    when: taskConditionSchema.optional(),
  })
  .strict();
export type ScannerTask = z.infer<typeof scannerTaskSchema>;

export const scannerJobSchema = z
  .object({
    schemaVersion: z.literal(1),
    run: z
      .object({
        id: z.string().min(1).max(200),
        tenantId: z.string().min(1).max(160),
        projectId: z.string().min(1).max(160),
        engine: scannerEngineSchema,
        profile: z.enum(["audit", "quick", "standard", "deep"]),
        targets: z.array(z.string().min(1).max(2048)).min(1).max(100),
        objective: z.string().min(3).max(12_000),
        authorization: z
          .object({
            id: z.string().min(8).max(160),
            targetPatterns: z.array(z.string().min(1).max(2048)).min(1).max(500),
            operations: z.array(scopeOperationSchema).min(1),
            validFrom: z.iso.datetime(),
            validUntil: z.iso.datetime(),
            attested: z.literal(true),
          })
          .passthrough(),
        config: z.record(z.string(), z.unknown()),
      })
      .passthrough(),
  })
  .strict();

export type ScannerJob = z.infer<typeof scannerJobSchema>;

export interface ScannerExecutionResult {
  externalRunId?: string;
  summary: Record<string, unknown>;
  findings: FindingSubmission[];
  artifacts: [];
}

export function configuredTasks(
  config: Record<string, unknown>,
  key: "tasks" | "validationTasks",
): ScannerTask[] | undefined {
  if (config[key] === undefined) return undefined;
  return z.array(scannerTaskSchema).min(1).max(100).parse(config[key]);
}

export function profileTaskLimit(profile: RunProfile): number {
  return { audit: 10, quick: 20, standard: 50, deep: 100 }[profile];
}
