import http from "node:http";
import https from "node:https";
import type { IncomingHttpHeaders } from "node:http";
import { X509Certificate } from "node:crypto";
import { isIP } from "node:net";
import type { PeerCertificate } from "node:tls";

export class UpstreamHttpError extends Error {
  readonly statusCode: number;
  readonly responseBody: unknown;

  constructor(statusCode: number, responseBody: unknown) {
    super(`Upstream returned HTTP ${statusCode}`);
    this.statusCode = statusCode;
    this.responseBody = responseBody;
  }
}

export interface JsonRequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH";
  headers?: Record<string, string>;
  body?: unknown;
  timeoutMs: number;
  maxResponseBytes: number;
  maxRetries: number;
  ca?: Buffer;
  tlsServerName?: string;
}

export interface JsonResponse {
  statusCode: number;
  headers: IncomingHttpHeaders;
  body: unknown;
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, milliseconds);
    timer.unref();
  });
}

function retryableStatus(statusCode: number): boolean {
  return [408, 425, 429, 502, 503, 504].includes(statusCode);
}

function parseBody(raw: string): unknown {
  if (!raw) return {};
  try {
    return JSON.parse(raw) as unknown;
  } catch {
    return { text: raw.slice(0, 10_000) };
  }
}

// Some appliance scanners may issue a certificate whose numeric host is encoded as a DNS SAN
// instead of an IP SAN. Node correctly rejects that with checkHost(), so allow
// only an exact numeric DNS SAN as a narrow compatibility fallback.
export function matchesNumericDnsSan(expected: string, subjectAltName: string | undefined): boolean {
  if (isIP(expected) === 0 || !subjectAltName) return false;
  const wanted = `dns:${expected}`.toLowerCase();
  return subjectAltName.split(",").some((entry) => entry.trim().toLowerCase() === wanted);
}

function verifyDnsCertificateName(expected: string, certificate: PeerCertificate): Error | undefined {
  if (!certificate.raw) return new Error("Upstream TLS certificate did not include raw data");
  const parsed = new X509Certificate(certificate.raw);
  const matched = parsed.checkHost(expected, { subject: "never" })
    ?? (matchesNumericDnsSan(expected, parsed.subjectAltName) ? expected : undefined);
  return matched ? undefined : new Error(`Upstream TLS certificate is not valid for ${expected}`);
}

async function requestOnce(url: URL, options: JsonRequestOptions): Promise<JsonResponse> {
  const body = options.body === undefined ? undefined : JSON.stringify(options.body);
  const transport = url.protocol === "https:" ? https : http;
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error(`Unsupported upstream protocol: ${url.protocol}`);
  }

  return new Promise((resolve, reject) => {
    const request = transport.request(
      url,
      {
        method: options.method ?? "GET",
        headers: {
          accept: "application/json",
          ...(body === undefined
            ? {}
            : {
                "content-type": "application/json",
                "content-length": String(Buffer.byteLength(body)),
              }),
          ...options.headers,
        },
        ...(url.protocol === "https:" && options.ca ? { ca: options.ca } : {}),
        ...(url.protocol === "https:" && options.tlsServerName
          ? {
              servername: options.tlsServerName,
              checkServerIdentity: (_hostname: string, certificate: PeerCertificate) =>
                verifyDnsCertificateName(options.tlsServerName as string, certificate),
            }
          : {}),
      },
      (response) => {
        const chunks: Buffer[] = [];
        let bytes = 0;
        // Node can emit "error"/"aborted" on the *response* stream when the
        // upstream tears down mid-body; without listeners the promise would
        // never settle and the semaphore slot would leak forever.
        let settled = false;
        const settle = (fn: () => void) => {
          if (settled) return;
          settled = true;
          clearTimeout(watchdog);
          fn();
        };
        clearTimeout(watchdog);
        response.once("error", (error: Error) => settle(() => reject(error)));
        response.once("aborted", () => settle(() => reject(new Error("Upstream aborted the response"))));
        response.on("data", (chunk: Buffer | string) => {
          const value = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
          bytes += value.length;
          if (bytes > options.maxResponseBytes) {
            request.destroy(new Error(`Upstream response exceeded ${options.maxResponseBytes} bytes`));
            return;
          }
          chunks.push(value);
        });
        response.once("end", () => {
          const parsed = parseBody(Buffer.concat(chunks).toString("utf8"));
          const status = response.statusCode ?? 500;
          if (status < 200 || status >= 300) {
            settle(() => reject(new UpstreamHttpError(status, parsed)));
            return;
          }
          settle(() => resolve({ statusCode: status, headers: response.headers, body: parsed }));
        });
      },
    );
    // request.setTimeout is an *idle* timeout that gets cleared on socket close
    // and resets on traffic, so it cannot be the final backstop. Use one
    // wall-clock watchdog that always fires and a separate idle timer.
    const watchdog = setTimeout(() => {
      request.destroy(new Error(`Upstream request timed out after ${options.timeoutMs}ms`));
    }, options.timeoutMs);
    watchdog.unref?.();
    request.setTimeout(options.timeoutMs, () => {
      request.destroy(new Error(`Upstream request timed out after ${options.timeoutMs}ms`));
    });
    request.once("error", (error: Error) => {
      clearTimeout(watchdog);
      reject(error);
    });
    if (body !== undefined) request.write(body);
    request.end();
  });
}

export async function requestJsonResponse(
  url: URL,
  options: JsonRequestOptions,
): Promise<JsonResponse> {
  let lastError: unknown;
  for (let attempt = 0; attempt <= options.maxRetries; attempt += 1) {
    try {
      return await requestOnce(url, options);
    } catch (error) {
      lastError = error;
      const mayRetry =
        attempt < options.maxRetries &&
        (!(error instanceof UpstreamHttpError) || retryableStatus(error.statusCode));
      if (!mayRetry) throw error;
      await wait(Math.min(5000, 250 * 2 ** attempt));
    }
  }
  throw lastError;
}

export async function requestJson(url: URL, options: JsonRequestOptions): Promise<unknown> {
  return (await requestJsonResponse(url, options)).body;
}

export class Semaphore {
  readonly #limit: number;
  #active = 0;
  readonly #waiting: Array<() => void> = [];

  constructor(limit: number) {
    this.#limit = limit;
  }

  async run<T>(operation: () => Promise<T>): Promise<T> {
    if (this.#active >= this.#limit) {
      await new Promise<void>((resolve) => this.#waiting.push(resolve));
    }
    this.#active += 1;
    try {
      return await operation();
    } finally {
      this.#active -= 1;
      this.#waiting.shift()?.();
    }
  }

  snapshot(): { active: number; queued: number; limit: number } {
    return { active: this.#active, queued: this.#waiting.length, limit: this.#limit };
  }
}
