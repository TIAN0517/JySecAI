import { z } from "zod";

const booleanFromEnv = z
  .enum(["true", "false"])
  .default("false")
  .transform((value) => value === "true");

const optionalBooleanFromEnv = z
  .enum(["true", "false"])
  .optional()
  .transform((value) => (value === undefined ? undefined : value === "true"));

const optionalUrlFromEnv = z.preprocess(
  (value) => (typeof value === "string" && value.trim() === "" ? undefined : value),
  z.url().optional(),
);

const envSchema = z
  .object({
    NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
    JYSEC_HOST: z.string().default("0.0.0.0"),
    JYSEC_PORT: z.coerce.number().int().min(1).max(65_535).default(8787),
    JYSEC_LOG_LEVEL: z.enum(["fatal", "error", "warn", "info", "debug", "trace", "silent"]).default("info"),
    JYSEC_STORE: z.enum(["memory", "postgres"]).default("memory"),
    DATABASE_URL: z.string().optional(),
    REDIS_URL: z.string().default("redis://127.0.0.1:6379/0"),
    JYSEC_JWT_SECRET: z.string().min(32).default("development-only-change-this-secret-now"),
    JYSEC_JWKS_URL: optionalUrlFromEnv,
    JYSEC_JWT_ISSUER: z.string().min(1).default("jysecai"),
    JYSEC_JWT_AUDIENCE: z.string().min(1).default("jysec-platform"),
    JYSEC_DEV_AUTH: booleanFromEnv,
    JYSEC_JOB_SIGNING_SECRET: z.string().min(32).default("development-job-signing-secret-change"),
    JYSEC_METRICS_TOKEN: z.string().min(32).optional(),
    JYSEC_RUNS_ROOT: z.string().default("./var/runs"),
    JYSEC_PUBLIC_BASE_URL: z.url().default("http://localhost:8787"),
    JYSEC_INTERNAL_CALLBACK_BASE_URL: z.url().optional(),
    STRIX_BIN: z.string().min(1).default("strix"),
    STRIX_LLM: z.string().optional(),
    LLM_API_KEY: z.string().optional(),
    JYSEC_ENGINE_STRIX_ENABLED: optionalBooleanFromEnv,
    CYBERSTRIKE_BASE_URL: z.url().default("http://127.0.0.1:8080"),
    CYBERSTRIKE_SERVICE_TOKEN: z.string().optional(),
    JYSEC_ENGINE_HEXSTRIKE_URL: optionalUrlFromEnv,
    JYSEC_ENGINE_KALI_MCP_URL: optionalUrlFromEnv,
    JYSEC_ENGINE_AWVS_URL: optionalUrlFromEnv,
    JYSEC_ENGINE_PROMPTFOO_URL: optionalUrlFromEnv,
    JYSEC_ENGINE_PYRIT_URL: optionalUrlFromEnv,
    JYSEC_ENGINE_GISKARD_URL: optionalUrlFromEnv,
    JYSEC_ENGINE_ART_URL: optionalUrlFromEnv,
    JYSEC_ENGINE_HUMANBOUND_URL: optionalUrlFromEnv,
    JYSEC_ENGINE_AD_AUDIT_URL: optionalUrlFromEnv,
    JYSEC_ENGINE_ADAPTER_TOKEN: z.string().optional(),
    STRIPE_SECRET_KEY: z.string().optional(),
    STRIPE_WEBHOOK_SECRET: z.string().optional(),
    STRIPE_PRICE_PROFESSIONAL: z.string().optional(),
    STRIPE_PRICE_BUSINESS: z.string().optional(),
  })
  .superRefine((env, ctx) => {
    if (env.JYSEC_STORE === "postgres" && !env.DATABASE_URL) {
      ctx.addIssue({
        code: "custom",
        path: ["DATABASE_URL"],
        message: "DATABASE_URL is required when JYSEC_STORE=postgres",
      });
    }
    if (env.NODE_ENV === "production" && env.JYSEC_DEV_AUTH) {
      ctx.addIssue({
        code: "custom",
        path: ["JYSEC_DEV_AUTH"],
        message: "JYSEC_DEV_AUTH must be false in production",
      });
    }
    if (
      env.NODE_ENV === "production" &&
      !env.JYSEC_JWKS_URL &&
      env.JYSEC_JWT_SECRET.startsWith("development")
    ) {
      ctx.addIssue({
        code: "custom",
        path: ["JYSEC_JWT_SECRET"],
        message: "A production JWT secret must be configured",
      });
    }
    if (env.NODE_ENV === "production" && env.JYSEC_JOB_SIGNING_SECRET.startsWith("development")) {
      ctx.addIssue({
        code: "custom",
        path: ["JYSEC_JOB_SIGNING_SECRET"],
        message: "A production job-signing secret must be configured",
      });
    }
    if (env.NODE_ENV === "production" && env.JYSEC_STORE !== "postgres") {
      ctx.addIssue({
        code: "custom",
        path: ["JYSEC_STORE"],
        message: "Production deployments must use PostgreSQL",
      });
    }
    if (env.NODE_ENV === "production" && !env.JYSEC_METRICS_TOKEN) {
      ctx.addIssue({
        code: "custom",
        path: ["JYSEC_METRICS_TOKEN"],
        message: "A production metrics token must be configured",
      });
    }
    if (env.NODE_ENV === "production" && env.JYSEC_JWT_SECRET === env.JYSEC_JOB_SIGNING_SECRET) {
      ctx.addIssue({
        code: "custom",
        path: ["JYSEC_JOB_SIGNING_SECRET"],
        message: "JWT and job-signing secrets must be different",
      });
    }
    if (env.NODE_ENV === "production" && new URL(env.JYSEC_PUBLIC_BASE_URL).protocol !== "https:") {
      ctx.addIssue({
        code: "custom",
        path: ["JYSEC_PUBLIC_BASE_URL"],
        message: "Production public base URL must use HTTPS",
      });
    }
  });

export type AppConfig = ReturnType<typeof loadConfig>;

export function loadConfig(source: NodeJS.ProcessEnv = process.env) {
  const parsed = envSchema.parse(source);
  return Object.freeze({
    environment: parsed.NODE_ENV,
    host: parsed.JYSEC_HOST,
    port: parsed.JYSEC_PORT,
    logLevel: parsed.JYSEC_LOG_LEVEL,
    store: parsed.JYSEC_STORE,
    databaseUrl: parsed.DATABASE_URL,
    redisUrl: parsed.REDIS_URL,
    jwtSecret: parsed.JYSEC_JWT_SECRET,
    jwksUrl: parsed.JYSEC_JWKS_URL,
    jwtIssuer: parsed.JYSEC_JWT_ISSUER,
    jwtAudience: parsed.JYSEC_JWT_AUDIENCE,
    devAuth: parsed.JYSEC_DEV_AUTH,
    jobSigningSecret: parsed.JYSEC_JOB_SIGNING_SECRET,
    metricsToken: parsed.JYSEC_METRICS_TOKEN,
    runsRoot: parsed.JYSEC_RUNS_ROOT,
    publicBaseUrl: parsed.JYSEC_PUBLIC_BASE_URL,
    internalCallbackBaseUrl: parsed.JYSEC_INTERNAL_CALLBACK_BASE_URL ?? parsed.JYSEC_PUBLIC_BASE_URL,
    engines: {
      strixBin: parsed.STRIX_BIN,
      strixLlm: parsed.STRIX_LLM,
      llmApiKey: parsed.LLM_API_KEY,
      strixEnabled: parsed.JYSEC_ENGINE_STRIX_ENABLED ?? parsed.NODE_ENV !== "production",
      cyberstrikeBaseUrl: parsed.CYBERSTRIKE_BASE_URL,
      cyberstrikeServiceToken: parsed.CYBERSTRIKE_SERVICE_TOKEN,
      adapterUrls: {
        hexstrike: parsed.JYSEC_ENGINE_HEXSTRIKE_URL,
        "kali-mcp": parsed.JYSEC_ENGINE_KALI_MCP_URL,
        awvs: parsed.JYSEC_ENGINE_AWVS_URL,
        promptfoo: parsed.JYSEC_ENGINE_PROMPTFOO_URL,
        pyrit: parsed.JYSEC_ENGINE_PYRIT_URL,
        giskard: parsed.JYSEC_ENGINE_GISKARD_URL,
        art: parsed.JYSEC_ENGINE_ART_URL,
        humanbound: parsed.JYSEC_ENGINE_HUMANBOUND_URL,
        "ad-audit": parsed.JYSEC_ENGINE_AD_AUDIT_URL,
      },
      adapterToken: parsed.JYSEC_ENGINE_ADAPTER_TOKEN,
    },
    stripe: {
      secretKey: parsed.STRIPE_SECRET_KEY,
      webhookSecret: parsed.STRIPE_WEBHOOK_SECRET,
      professionalPriceId: parsed.STRIPE_PRICE_PROFESSIONAL,
      businessPriceId: parsed.STRIPE_PRICE_BUSINESS,
    },
  });
}
