import { z } from "zod";

export const engineIds = [
  "strix",
  "jysecai",
  "hexstrike",
  "kali-mcp",
  "promptfoo",
  "pyrit",
  "giskard",
  "art",
  "humanbound",
  "ad-audit",
] as const;

export const engineIdSchema = z.enum(engineIds);
export type EngineId = z.infer<typeof engineIdSchema>;

export const runProfiles = ["audit", "quick", "standard", "deep"] as const;
export const runProfileSchema = z.enum(runProfiles);
export type RunProfile = z.infer<typeof runProfileSchema>;

export const runStatuses = [
  "awaiting_approval",
  "queued",
  "dispatching",
  "running",
  "paused",
  "completed",
  "failed",
  "cancelled",
  "budget_paused",
] as const;

export const runStatusSchema = z.enum(runStatuses);
export type RunStatus = z.infer<typeof runStatusSchema>;

export const scopeOperationSchema = z.enum([
  "passive_discovery",
  "active_scan",
  "exploit_validation",
  "credential_audit",
  "source_review",
  "ai_red_team",
]);
export type ScopeOperation = z.infer<typeof scopeOperationSchema>;

export const authorizationScopeSchema = z
  .object({
    id: z.string().min(8).max(160),
    projectId: z.string().min(1).max(160),
    tenantId: z.string().min(1).max(160),
    targetPatterns: z.array(z.string().min(1).max(2048)).min(1).max(500),
    operations: z.array(scopeOperationSchema).min(1),
    validFrom: z.iso.datetime(),
    validUntil: z.iso.datetime(),
    approvedBy: z.string().min(1).max(320),
    attested: z.literal(true),
    notes: z.string().max(4000).optional(),
  })
  .strict();
export type AuthorizationScope = z.infer<typeof authorizationScopeSchema>;

export const createRunSchema = z
  .object({
    projectId: z.string().min(1).max(160),
    engine: engineIdSchema,
    profile: runProfileSchema.default("standard"),
    targets: z.array(z.string().min(1).max(2048)).min(1).max(100),
    objective: z.string().min(3).max(12000),
    authorization: authorizationScopeSchema,
    config: z.record(z.string(), z.unknown()).default({}),
    idempotencyKey: z.string().min(8).max(200),
  })
  .strict();
export type CreateRunInput = z.infer<typeof createRunSchema>;

export interface ActorContext {
  tenantId: string;
  userId: string;
  email?: string;
  roles: string[];
  plan: PlanId;
  requestId: string;
}

export const planIds = ["community", "professional", "business", "enterprise"] as const;
export const planIdSchema = z.enum(planIds);
export type PlanId = z.infer<typeof planIdSchema>;

export interface EngineDescriptor {
  id: EngineId;
  name: string;
  category: "appsec" | "ai-security" | "ml-security" | "identity";
  maturity: "core" | "optional" | "experimental";
  profiles: readonly RunProfile[];
  requiredOperation: ScopeOperation;
  supportedOperations: readonly ScopeOperation[];
  active: boolean;
  status: "ready" | "unconfigured";
  reason: string;
  connector: "native" | "http" | "worker";
  description: string;
}

export type EngineCatalog = Readonly<Record<EngineId, EngineDescriptor>>;

export interface PlanEntitlements {
  id: PlanId;
  displayName: string;
  monthlyCredits: number;
  maxConcurrentRuns: number;
  engines: readonly EngineId[];
  auditRetentionDays: number;
  hitl: boolean;
  sso: boolean;
  privateWorkers: boolean;
}

export interface SecurityRun {
  id: string;
  tenantId: string;
  projectId: string;
  actorUserId: string;
  engine: EngineId;
  profile: RunProfile;
  targets: string[];
  objective: string;
  authorization: AuthorizationScope;
  config: Record<string, unknown>;
  status: RunStatus;
  statusReason?: string;
  estimatedCredits: number;
  reservedCredits: number;
  externalRunId?: string;
  idempotencyKey: string;
  createdAt: string;
  updatedAt: string;
  startedAt?: string;
  finishedAt?: string;
}

export const runEventTypes = [
  "run.created",
  "approval.required",
  "approval.granted",
  "run.queued",
  "run.dispatching",
  "run.started",
  "run.progress",
  "run.paused",
  "run.completed",
  "run.failed",
  "run.cancelled",
  "finding.published",
  "artifact.published",
  "usage.recorded",
] as const;
export type RunEventType = (typeof runEventTypes)[number];

export interface RunEvent {
  id: string;
  tenantId: string;
  runId: string;
  sequence: number;
  type: RunEventType;
  at: string;
  actorUserId?: string;
  data: Record<string, unknown>;
}

export const findingStatuses = ["suspected", "confirmed", "inconclusive", "resolved"] as const;
export type FindingStatus = (typeof findingStatuses)[number];

export interface Finding {
  id: string;
  tenantId: string;
  projectId: string;
  runId: string;
  engine: EngineId;
  engineVersion: string;
  testCaseId?: string;
  category: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  confidence: number;
  status: FindingStatus;
  evidenceRefs: string[];
  reproductionSummary?: string;
  counterevidence?: string;
  remediation?: string;
  fingerprint: string;
  createdAt: string;
}

export const findingSubmissionSchema = z
  .object({
    engineVersion: z.string().min(1).max(160),
    testCaseId: z.string().min(1).max(320).optional(),
    category: z.string().min(1).max(320),
    title: z.string().min(1).max(1000),
    severity: z.enum(["critical", "high", "medium", "low", "info"]),
    confidence: z.number().min(0).max(1),
    status: z.enum(findingStatuses),
    evidenceRefs: z.array(z.string().min(1).max(2048)).max(100).default([]),
    reproductionSummary: z.string().max(12000).optional(),
    counterevidence: z.string().max(12000).optional(),
    remediation: z.string().max(12000).optional(),
    fingerprint: z.string().min(8).max(256).regex(/^[a-zA-Z0-9:._-]+$/u).optional(),
  })
  .strict();
export type FindingSubmission = z.infer<typeof findingSubmissionSchema>;

export interface Artifact {
  id: string;
  tenantId: string;
  projectId: string;
  runId: string;
  kind: string;
  objectKey: string;
  sha256: string;
  mediaType: string;
  sizeBytes: number;
  encrypted: boolean;
  createdAt: string;
}

export const artifactSubmissionSchema = z
  .object({
    kind: z.string().min(1).max(160),
    objectKey: z.string().min(1).max(2048),
    sha256: z.string().regex(/^[a-f0-9]{64}$/u),
    mediaType: z.string().min(1).max(320),
    sizeBytes: z.number().int().min(0).max(Number.MAX_SAFE_INTEGER),
    encrypted: z.literal(true),
  })
  .strict();
export type ArtifactSubmission = z.infer<typeof artifactSubmissionSchema>;

export interface UsageLedgerEntry {
  id: string;
  tenantId: string;
  runId: string;
  period: string;
  kind: "reservation" | "debit" | "refund" | "adjustment";
  credits: number;
  idempotencyKey: string;
  createdAt: string;
}

export interface TenantSubscription {
  tenantId: string;
  planId: PlanId;
  provider: "manual" | "stripe" | "license";
  providerCustomerId?: string;
  providerSubscriptionId?: string;
  status: string;
  currentPeriodEnd?: string;
  updatedAt: string;
}

export interface DispatchJob {
  schemaVersion: 1;
  run: SecurityRun;
  callbackBaseUrl: string;
  issuedAt: string;
  signature: string;
}

export interface Page<T> {
  items: T[];
  nextCursor?: string;
}
