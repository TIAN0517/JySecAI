import { z } from "zod";

import { parseProxyPool } from "./proxy-pool.js";

const optionalUrl = z.preprocess(
  (value) => (typeof value === "string" && value.trim() === "" ? undefined : value),
  z.url().optional(),
);

const optionalString = z.preprocess(
  (value) => (typeof value === "string" && value.trim() === "" ? undefined : value),
  z.string().optional(),
);

const envSchema = z.object({
  JYSEC_LOG_LEVEL: z.enum(["fatal", "error", "warn", "info", "debug", "trace", "silent"]).default("info"),
  JYSEC_SCANNER_ADAPTER_HOST: z.string().default("127.0.0.1"),
  JYSEC_SCANNER_ADAPTER_PORT: z.coerce.number().int().min(1).max(65_535).default(8790),
  JYSEC_ENGINE_ADAPTER_TOKEN: optionalString,
  JYSEC_HEXSTRIKE_API_URL: optionalUrl,
  JYSEC_KALI_API_URL: optionalUrl,
  JYSEC_SCANNER_MAX_CONCURRENT_PER_ENGINE: z.coerce.number().int().min(1).max(32).default(2),
  JYSEC_SCANNER_REQUEST_TIMEOUT_SECONDS: z.coerce.number().int().min(5).max(3600).default(300),
  JYSEC_SCANNER_MAX_RETRIES: z.coerce.number().int().min(0).max(8).default(3),
  JYSEC_SCANNER_MAX_RESPONSE_BYTES: z.coerce.number().int().min(65_536).max(100_000_000).default(10_000_000),
  JYSEC_PROXY_POOL: z.string().default(""),
});

export type ScannerAdapterConfig = ReturnType<typeof loadScannerAdapterConfig>;

export function loadScannerAdapterConfig(source: NodeJS.ProcessEnv = process.env) {
  const parsed = envSchema.parse(source);
  return Object.freeze({
    logLevel: parsed.JYSEC_LOG_LEVEL,
    host: parsed.JYSEC_SCANNER_ADAPTER_HOST,
    port: parsed.JYSEC_SCANNER_ADAPTER_PORT,
    adapterToken: parsed.JYSEC_ENGINE_ADAPTER_TOKEN,
    backends: Object.freeze({
      hexstrike: parsed.JYSEC_HEXSTRIKE_API_URL,
      kali: parsed.JYSEC_KALI_API_URL,
    }),
    maxConcurrentPerEngine: parsed.JYSEC_SCANNER_MAX_CONCURRENT_PER_ENGINE,
    requestTimeoutMs: parsed.JYSEC_SCANNER_REQUEST_TIMEOUT_SECONDS * 1000,
    maxRetries: parsed.JYSEC_SCANNER_MAX_RETRIES,
    maxResponseBytes: parsed.JYSEC_SCANNER_MAX_RESPONSE_BYTES,
    proxyPool: parseProxyPool(parsed.JYSEC_PROXY_POOL),
  });
}
