import { createSecretKey, timingSafeEqual } from "node:crypto";

import type { FastifyReply, FastifyRequest } from "fastify";
import { createRemoteJWKSet, jwtVerify } from "jose";

import type { AppConfig } from "../config.js";
import { DomainError } from "../core/errors.js";
import { planIdSchema, type ActorContext } from "../core/types.js";

declare module "fastify" {
  interface FastifyRequest {
    actor?: ActorContext;
  }
}

function csv(value: string | undefined): string[] {
  return (value ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function buildAuthenticator(config: AppConfig) {
  const key = config.jwksUrl
    ? createRemoteJWKSet(new URL(config.jwksUrl), {
        cooldownDuration: 30_000,
        cacheMaxAge: 10 * 60_000,
        timeoutDuration: 5_000,
      })
    : createSecretKey(Buffer.from(config.jwtSecret, "utf8"));
  const algorithms = config.jwksUrl
    ? ["RS256", "PS256", "ES256", "EdDSA"]
    : ["HS256"];

  return async function authenticate(request: FastifyRequest, _reply: FastifyReply): Promise<void> {
    if (config.devAuth) {
      const tenantId = String(request.headers["x-jysec-tenant"] ?? "dev-tenant").trim();
      const userId = String(request.headers["x-jysec-user"] ?? "dev-user").trim();
      if (!tenantId || !userId) throw new DomainError("invalid_identity", "Development identity is invalid", 401);
      request.actor = {
        tenantId,
        userId,
        roles: csv(String(request.headers["x-jysec-roles"] ?? "owner,admin,security_approver")),
        plan: planIdSchema.catch("community").parse(request.headers["x-jysec-plan"]),
        requestId: request.id,
      };
      return;
    }

    const authorization = request.headers.authorization;
    if (!authorization?.startsWith("Bearer ")) {
      throw new DomainError("authentication_required", "A bearer access token is required", 401);
    }
    const token = authorization.slice("Bearer ".length).trim();
    try {
      const verified = await jwtVerify(token, key, {
        algorithms,
        issuer: config.jwtIssuer,
        audience: config.jwtAudience,
        clockTolerance: 5,
      });
      const tenantId = String(verified.payload.tenant_id ?? "").trim();
      const userId = String(verified.payload.sub ?? "").trim();
      const roles = Array.isArray(verified.payload.roles)
        ? verified.payload.roles.map(String).filter(Boolean)
        : [];
      if (!tenantId || !userId) throw new Error("required identity claims are missing");
      const email = typeof verified.payload.email === "string" ? verified.payload.email : undefined;
      request.actor = {
        tenantId,
        userId,
        ...(email !== undefined ? { email } : {}),
        roles,
        plan: planIdSchema.catch("community").parse(verified.payload.plan),
        requestId: request.id,
      };
    } catch {
      throw new DomainError("invalid_token", "Access token is invalid or expired", 401);
    }
  };
}

export function requireActor(request: FastifyRequest): ActorContext {
  if (!request.actor) throw new DomainError("authentication_required", "Authentication is required", 401);
  return request.actor;
}

export function workerTokenMatches(request: FastifyRequest, expected: string): boolean {
  const supplied = String(request.headers["x-jysec-worker-token"] ?? "");
  const suppliedBuffer = Buffer.from(supplied);
  const expectedBuffer = Buffer.from(expected);
  return suppliedBuffer.length === expectedBuffer.length && timingSafeEqual(suppliedBuffer, expectedBuffer);
}

export function bearerTokenMatches(request: FastifyRequest, expected: string | undefined): boolean {
  if (!expected) return true;
  const authorization = String(request.headers.authorization ?? "");
  const supplied = authorization.startsWith("Bearer ") ? authorization.slice(7).trim() : "";
  const suppliedBuffer = Buffer.from(supplied);
  const expectedBuffer = Buffer.from(expected);
  return suppliedBuffer.length === expectedBuffer.length && timingSafeEqual(suppliedBuffer, expectedBuffer);
}
