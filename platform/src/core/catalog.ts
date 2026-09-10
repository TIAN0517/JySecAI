import type { AppConfig } from "../config.js";
import {
  engineIds,
  type EngineCatalog,
  type EngineDescriptor,
  type EngineId,
  type PlanEntitlements,
  type PlanId,
  type RunProfile,
} from "./types.js";

type EngineDefinition = Omit<EngineDescriptor, "active" | "status" | "reason">;
type EngineAvailability = Pick<EngineDescriptor, "active" | "status" | "reason">;

const engineDefinitions: Readonly<Record<EngineId, EngineDefinition>> = Object.freeze({
  strix: {
    id: "strix",
    name: "Strix Autonomous Pentest",
    category: "appsec",
    maturity: "core",
    profiles: ["quick", "standard", "deep"],
    requiredOperation: "active_scan",
    supportedOperations: ["active_scan", "exploit_validation", "source_review"],
    connector: "worker",
    description: "Sandboxed autonomous application, API and source security validation.",
  },
  jysecai: {
    id: "jysecai",
    name: "Jy Workflow Orchestrator",
    category: "appsec",
    maturity: "core",
    profiles: ["audit", "quick", "standard", "deep"],
    requiredOperation: "active_scan",
    supportedOperations: ["passive_discovery", "active_scan", "exploit_validation", "credential_audit", "source_review"],
    connector: "http",
    description: "Governed project, workflow, evidence and attack-chain execution plane.",
  },
  hexstrike: {
    id: "hexstrike",
    name: "HexStrike AI",
    category: "appsec",
    maturity: "optional",
    profiles: ["audit", "quick", "standard", "deep"],
    requiredOperation: "active_scan",
    supportedOperations: ["passive_discovery", "active_scan", "exploit_validation", "credential_audit"],
    connector: "worker",
    description: "Remote Kali tool orchestration with normalized findings and conditional validation tasks.",
  },
  "kali-mcp": {
    id: "kali-mcp",
    name: "MCP Kali Server",
    category: "appsec",
    maturity: "optional",
    profiles: ["audit", "quick", "standard", "deep"],
    requiredOperation: "active_scan",
    supportedOperations: ["passive_discovery", "active_scan", "exploit_validation", "credential_audit"],
    connector: "worker",
    description: "TriV3 Kali API and MCP tool fabric with governed execution and evidence ingestion.",
  },
  promptfoo: {
    id: "promptfoo",
    name: "Promptfoo CI Red Team",
    category: "ai-security",
    maturity: "core",
    profiles: ["quick", "standard", "deep"],
    requiredOperation: "ai_red_team",
    supportedOperations: ["ai_red_team"],
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
    supportedOperations: ["ai_red_team"],
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
    supportedOperations: ["ai_red_team"],
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
    supportedOperations: ["ai_red_team"],
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
    supportedOperations: ["ai_red_team"],
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
    supportedOperations: ["credential_audit"],
    connector: "worker",
    description: "Read-only SPN, Kerberos encryption, pre-authentication and event analytics.",
  },
});

const unconfigured = (reason: string): EngineAvailability => ({
  active: false,
  status: "unconfigured",
  reason,
});

const ready = (reason: string): EngineAvailability => ({ active: true, status: "ready", reason });

function catalogWithAvailability(availability: Readonly<Record<EngineId, EngineAvailability>>): EngineCatalog {
  return Object.freeze(
    Object.fromEntries(
      engineIds.map((id) => [id, Object.freeze({ ...engineDefinitions[id], ...availability[id] })]),
    ) as Record<EngineId, EngineDescriptor>,
  );
}

const notEvaluated = Object.fromEntries(
  engineIds.map((id) => [id, unconfigured("Runtime engine availability has not been evaluated.")]),
) as Record<EngineId, EngineAvailability>;

/** Static metadata catalog for policy evaluation outside an application runtime. */
export const engineCatalog: EngineCatalog = catalogWithAvailability(notEvaluated);

function adapterAvailability(endpoint: string | undefined, environmentKey: string): EngineAvailability {
  return endpoint
    ? ready(`${environmentKey} is configured.`)
    : unconfigured(`${environmentKey} must be set to the adapter service URL.`);
}

/** Build the truthful catalog used by both the API response and run admission. */
export function createRuntimeEngineCatalog(config: AppConfig): EngineCatalog {
  const jysecaiToken = config.engines.jysecaiServiceToken?.trim();
  return catalogWithAvailability({
    strix: config.engines.strixEnabled
      ? ready("JYSEC_ENGINE_STRIX_ENABLED is enabled for this deployment.")
      : unconfigured("JYSEC_ENGINE_STRIX_ENABLED must be explicitly enabled for this deployment."),
    jysecai: jysecaiToken
      ? ready("JYSECAI_SERVICE_TOKEN is configured.")
      : unconfigured("JYSECAI_SERVICE_TOKEN is required to authenticate with the workflow service."),
    hexstrike: adapterAvailability(config.engines.adapterUrls.hexstrike, "JYSEC_ENGINE_HEXSTRIKE_URL"),
    "kali-mcp": adapterAvailability(
      config.engines.adapterUrls["kali-mcp"],
      "JYSEC_ENGINE_KALI_MCP_URL",
    ),
    promptfoo: adapterAvailability(
      config.engines.adapterUrls.promptfoo,
      "JYSEC_ENGINE_PROMPTFOO_URL",
    ),
    pyrit: adapterAvailability(config.engines.adapterUrls.pyrit, "JYSEC_ENGINE_PYRIT_URL"),
    giskard: adapterAvailability(config.engines.adapterUrls.giskard, "JYSEC_ENGINE_GISKARD_URL"),
    art: adapterAvailability(config.engines.adapterUrls.art, "JYSEC_ENGINE_ART_URL"),
    humanbound: adapterAvailability(
      config.engines.adapterUrls.humanbound,
      "JYSEC_ENGINE_HUMANBOUND_URL",
    ),
    "ad-audit": adapterAvailability(
      config.engines.adapterUrls["ad-audit"],
      "JYSEC_ENGINE_AD_AUDIT_URL",
    ),
  });
}

const allEngines = [...engineIds];

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
    engines: [
      "strix",
      "jysecai",
      "hexstrike",
      "kali-mcp",
      "promptfoo",
      "giskard",
      "humanbound",
      "ad-audit",
    ],
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
  jysecai: 1,
  hexstrike: 2,
  "kali-mcp": 2,
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
