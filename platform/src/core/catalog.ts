import type { EngineDescriptor, EngineId, PlanEntitlements, PlanId, RunProfile } from "./types.js";

export const engineCatalog: Readonly<Record<EngineId, EngineDescriptor>> = Object.freeze({
  strix: {
    id: "strix",
    name: "Strix Autonomous Pentest",
    category: "appsec",
    maturity: "core",
    profiles: ["quick", "standard", "deep"],
    requiredOperation: "active_scan",
    active: true,
    connector: "worker",
    description: "Sandboxed autonomous application, API and source security validation.",
  },
  cyberstrike: {
    id: "cyberstrike",
    name: "Jy Workflow Orchestrator",
    category: "appsec",
    maturity: "core",
    profiles: ["audit", "quick", "standard", "deep"],
    requiredOperation: "active_scan",
    active: true,
    connector: "http",
    description: "Governed project, workflow, evidence and attack-chain execution plane.",
  },
  promptfoo: {
    id: "promptfoo",
    name: "Promptfoo CI Red Team",
    category: "ai-security",
    maturity: "core",
    profiles: ["quick", "standard", "deep"],
    requiredOperation: "ai_red_team",
    active: true,
    connector: "worker",
    description: "Repeatable LLM, RAG and prompt-security regression testing.",
  },
  pyrit: {
    id: "pyrit",
    name: "PyRIT Campaign",
    category: "ai-security",
    maturity: "core",
    profiles: ["standard", "deep"],
    requiredOperation: "ai_red_team",
    active: true,
    connector: "worker",
    description: "Multi-turn and multimodal generative-AI risk campaign orchestration.",
  },
  giskard: {
    id: "giskard",
    name: "Giskard Agent Evaluation",
    category: "ai-security",
    maturity: "core",
    profiles: ["quick", "standard", "deep"],
    requiredOperation: "ai_red_team",
    active: true,
    connector: "worker",
    description: "Dynamic agent and RAG quality, safety and regression evaluation.",
  },
  art: {
    id: "art",
    name: "Adversarial Robustness Toolbox",
    category: "ml-security",
    maturity: "core",
    profiles: ["audit", "standard", "deep"],
    requiredOperation: "ai_red_team",
    active: true,
    connector: "worker",
    description: "Isolated CPU/GPU adversarial machine-learning robustness evaluation.",
  },
  humanbound: {
    id: "humanbound",
    name: "Humanbound Agent Boundary",
    category: "ai-security",
    maturity: "optional",
    profiles: ["quick", "standard", "deep"],
    requiredOperation: "ai_red_team",
    active: true,
    connector: "worker",
    description: "Agent tool-boundary, indirect-injection and permission-abuse testing.",
  },
  "ad-audit": {
    id: "ad-audit",
    name: "Active Directory Risk Audit",
    category: "identity",
    maturity: "core",
    profiles: ["audit", "standard"],
    requiredOperation: "credential_audit",
    active: true,
    connector: "worker",
    description: "Read-only SPN, Kerberos encryption, pre-authentication and event analytics.",
  },
});

const allEngines = Object.keys(engineCatalog) as EngineId[];

export const planCatalog: Readonly<Record<PlanId, PlanEntitlements>> = Object.freeze({
  community: {
    id: "community",
    displayName: "Community",
    monthlyCredits: 50,
    maxConcurrentRuns: 1,
    engines: ["promptfoo", "ad-audit"],
    auditRetentionDays: 7,
    hitl: true,
    sso: false,
    privateWorkers: false,
  },
  professional: {
    id: "professional",
    displayName: "Professional",
    monthlyCredits: 2_500,
    maxConcurrentRuns: 5,
    engines: ["strix", "cyberstrike", "promptfoo", "giskard", "humanbound", "ad-audit"],
    auditRetentionDays: 90,
    hitl: true,
    sso: false,
    privateWorkers: false,
  },
  business: {
    id: "business",
    displayName: "Business",
    monthlyCredits: 20_000,
    maxConcurrentRuns: 25,
    engines: allEngines,
    auditRetentionDays: 365,
    hitl: true,
    sso: true,
    privateWorkers: true,
  },
  enterprise: {
    id: "enterprise",
    displayName: "Enterprise Sovereign",
    monthlyCredits: 100_000,
    maxConcurrentRuns: 100,
    engines: allEngines,
    auditRetentionDays: 2_555,
    hitl: true,
    sso: true,
    privateWorkers: true,
  },
});

const profileWeight: Record<RunProfile, number> = {
  audit: 2,
  quick: 5,
  standard: 20,
  deep: 60,
};

const engineWeight: Record<EngineId, number> = {
  strix: 2,
  cyberstrike: 1,
  promptfoo: 1,
  pyrit: 2,
  giskard: 1,
  art: 3,
  humanbound: 1,
  "ad-audit": 1,
};

export function estimateRunCredits(engine: EngineId, profile: RunProfile, targetCount: number): number {
  const boundedTargets = Math.max(1, Math.min(targetCount, 100));
  return Math.ceil(profileWeight[profile] * engineWeight[engine] * Math.sqrt(boundedTargets));
}
