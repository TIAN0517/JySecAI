import type {
  Artifact,
  Finding,
  Page,
  PlanId,
  RunEvent,
  SecurityRun,
  TenantSubscription,
  UsageLedgerEntry,
} from "./types.js";

export interface ListRunsFilter {
  tenantId: string;
  projectId?: string;
  limit: number;
  cursor?: string;
}

export interface RunPatch {
  status?: SecurityRun["status"];
  statusReason?: string;
  externalRunId?: string;
  startedAt?: string;
  finishedAt?: string;
  updatedAt: string;
  expectedStatus?: SecurityRun["status"];
}

export interface ControlPlaneStore {
  migrate(): Promise<void>;
  close(): Promise<void>;
  withTenantRunLock<T>(tenantId: string, operation: () => Promise<T>): Promise<T>;
  createRun(run: SecurityRun): Promise<{ run: SecurityRun; created: boolean }>;
  getRunByIdempotencyKey(tenantId: string, idempotencyKey: string): Promise<SecurityRun | null>;
  getRun(tenantId: string, runId: string): Promise<SecurityRun | null>;
  listRuns(filter: ListRunsFilter): Promise<Page<SecurityRun>>;
  updateRun(tenantId: string, runId: string, patch: RunPatch): Promise<SecurityRun>;
  countActiveRuns(tenantId: string): Promise<number>;
  appendEvent(event: Omit<RunEvent, "sequence">): Promise<RunEvent>;
  listEvents(tenantId: string, runId: string, afterSequence: number, limit: number): Promise<RunEvent[]>;
  appendUsage(entry: UsageLedgerEntry): Promise<{ entry: UsageLedgerEntry; created: boolean }>;
  sumUsage(tenantId: string, period: string): Promise<number>;
  getTenantPlan(tenantId: string): Promise<PlanId>;
  setTenantPlan(tenantId: string, plan: PlanId): Promise<void>;
  getSubscription(tenantId: string): Promise<TenantSubscription | null>;
  upsertSubscription(subscription: TenantSubscription): Promise<void>;
  upsertFinding(finding: Finding): Promise<Finding>;
  listProjectFindings(tenantId: string, projectId: string, limit: number): Promise<Finding[]>;
  appendArtifact(artifact: Artifact): Promise<{ artifact: Artifact; created: boolean }>;
  listRunArtifacts(tenantId: string, runId: string, limit: number): Promise<Artifact[]>;
}
