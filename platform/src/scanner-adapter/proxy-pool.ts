import net from "node:net";
import { createHash } from "node:crypto";

import type { ScannerAdapterConfig } from "./config.js";

export interface ProxyEndpoint {
  id: string;
  socksUrl: string;
  httpUrl: string;
  expectedIp?: string;
}

function parseEntry(value: string): ProxyEndpoint | undefined {
  const [id, socksUrl, httpUrl, expectedIp] = value.split("|").map((item) => item.trim());
  if (!id || !socksUrl || !httpUrl) return undefined;
  try {
    const socks = new URL(socksUrl);
    const http = new URL(httpUrl);
    if (!['socks5:', 'socks5h:'].includes(socks.protocol) || http.protocol !== 'http:') return undefined;
    if (!socks.hostname || !http.hostname || !Number.isInteger(Number(socks.port)) || !Number.isInteger(Number(http.port))) return undefined;
    return { id, socksUrl, httpUrl, ...(expectedIp ? { expectedIp } : {}) };
  } catch {
    return undefined;
  }
}

export function proxyPool(config: ScannerAdapterConfig): readonly ProxyEndpoint[] {
  return config.proxyPool;
}

function portAvailable(url: string): Promise<boolean> {
  const parsed = new URL(url);
  return new Promise((resolve) => {
    const socket = net.createConnection({ host: parsed.hostname, port: Number(parsed.port) });
    const finish = (value: boolean) => {
      socket.destroy();
      resolve(value);
    };
    socket.setTimeout(600, () => finish(false));
    socket.once("connect", () => finish(true));
    socket.once("error", () => finish(false));
  });
}

export async function selectProxy(config: ScannerAdapterConfig, runId: string): Promise<ProxyEndpoint | undefined> {
  const pool = proxyPool(config);
  if (!pool.length) return undefined;
  const offset = createHash("sha256").update(runId).digest().readUInt32BE(0) % pool.length;
  for (let step = 0; step < pool.length; step += 1) {
    const candidate = pool[(offset + step) % pool.length] as ProxyEndpoint;
    if (await portAvailable(candidate.socksUrl)) return candidate;
  }
  throw new Error("No healthy local VPS proxy tunnel is available");
}

export function parseProxyPool(value: string | undefined): readonly ProxyEndpoint[] {
  return Object.freeze((value ?? "").split(";").map((item) => parseEntry(item.trim())).filter((item): item is ProxyEndpoint => Boolean(item)));
}
