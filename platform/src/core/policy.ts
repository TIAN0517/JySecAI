import ipaddr from "ipaddr.js";

import { DomainError } from "./errors.js";
import type {
  AuthorizationScope,
  EngineDescriptor,
  RunProfile,
  ScopeOperation,
} from "./types.js";

export interface PolicyDecision {
  allowed: boolean;
  approvalRequired: boolean;
  normalizedTargets: string[];
  reasons: string[];
}

interface NormalizedTarget {
  original: string;
  value: string;
  hostname: string;
  kind: "url" | "host" | "ip";
}

function normalizeTarget(raw: string): NormalizedTarget {
  const original = raw.trim();
  if (!original || /[\u0000-\u001f\u007f]/u.test(original)) {
    throw new DomainError("invalid_target", "Target is empty or contains control characters");
  }
  if (original.length > 2048) {
    throw new DomainError("invalid_target", "Target exceeds 2048 characters");
  }

  if (/^[a-z][a-z0-9+.-]*:\/\//iu.test(original)) {
    let parsed: URL;
    try {
      parsed = new URL(original);
    } catch {
      throw new DomainError("invalid_target", `Invalid target URL: ${original}`);
    }
    if (!["http:", "https:"].includes(parsed.protocol)) {
      throw new DomainError("invalid_target", "Only HTTP and HTTPS URL targets are supported");
    }
    if (parsed.username || parsed.password) {
      throw new DomainError("invalid_target", "Credentials must not be embedded in target URLs");
    }
    const hostname = parsed.hostname.replace(/^\[|\]$/gu, "").toLowerCase();
    return { original, value: parsed.toString(), hostname, kind: ipaddr.isValid(hostname) ? "ip" : "url" };
  }

  const withoutPort = original.startsWith("[")
    ? original.slice(1, original.indexOf("]"))
    : original.replace(/:\d+$/u, "");
  const hostname = withoutPort.toLowerCase().replace(/\.$/u, "");
  if (!hostname || /[\s/@]/u.test(hostname)) {
    throw new DomainError("invalid_target", `Invalid host target: ${original}`);
  }
  return { original, value: original, hostname, kind: ipaddr.isValid(hostname) ? "ip" : "host" };
}

function domainPatternMatches(hostname: string, pattern: string): boolean {
  const normalized = pattern.toLowerCase().replace(/\.$/u, "");
  if (normalized.startsWith("*.")) {
    const suffix = normalized.slice(1);
    return hostname.endsWith(suffix) && hostname !== suffix.slice(1);
  }
  return hostname === normalized;
}

function cidrMatches(hostname: string, pattern: string): boolean {
  if (!ipaddr.isValid(hostname) || !pattern.includes("/")) return false;
  try {
    const address = ipaddr.parse(hostname);
    const [network, prefix] = ipaddr.parseCIDR(pattern);
    return address.kind() === network.kind() && address.match(network, prefix);
  } catch {
    return false;
  }
}

function targetMatchesPattern(target: NormalizedTarget, rawPattern: string): boolean {
  const pattern = rawPattern.trim();
  if (!pattern) return false;
  if (cidrMatches(target.hostname, pattern)) return true;

  if (/^[a-z][a-z0-9+.-]*:\/\//iu.test(pattern)) {
    try {
      const allowed = new URL(pattern);
      const candidate = new URL(
        target.kind === "url" ? target.value : `https://${target.hostname}`,
      );
      if (allowed.protocol !== candidate.protocol || allowed.hostname !== candidate.hostname) return false;
      if (allowed.port && allowed.port !== candidate.port) return false;
      const allowedPath = allowed.pathname.replace(/\*$/u, "");
      return candidate.pathname.startsWith(allowedPath);
    } catch {
      return false;
    }
  }

  return domainPatternMatches(target.hostname, pattern.replace(/:\d+$/u, ""));
}

export function evaluateRunPolicy(input: {
  tenantId: string;
  projectId: string;
  descriptor: EngineDescriptor;
  profile: RunProfile;
  targets: string[];
  authorization: AuthorizationScope;
  now?: Date;
}): PolicyDecision {
  const now = input.now ?? new Date();
  const scope = input.authorization;
  const reasons: string[] = [];

  if (scope.tenantId !== input.tenantId) reasons.push("authorization tenant mismatch");
  if (scope.projectId !== input.projectId) reasons.push("authorization project mismatch");
  if (new Date(scope.validFrom).getTime() > now.getTime()) reasons.push("authorization is not active yet");
  if (new Date(scope.validUntil).getTime() <= now.getTime()) reasons.push("authorization has expired");
  const supportedAuthorization = scope.operations.some((operation) =>
    input.descriptor.supportedOperations.includes(operation),
  );
  if (!supportedAuthorization) {
    reasons.push(`authorization does not permit an operation supported by ${input.descriptor.id}`);
  }
  if (!input.descriptor.profiles.includes(input.profile)) {
    reasons.push(`engine ${input.descriptor.id} does not support profile ${input.profile}`);
  }

  const normalized = input.targets.map(normalizeTarget);
  for (const target of normalized) {
    if (!scope.targetPatterns.some((pattern) => targetMatchesPattern(target, pattern))) {
      reasons.push(`target is outside authorized scope: ${target.original}`);
    }
  }

  const passiveOnly = input.profile === "audit" && input.descriptor.id === "ad-audit";
  const approvalRequired = !passiveOnly;
  return {
    allowed: reasons.length === 0,
    approvalRequired,
    normalizedTargets: normalized.map((target) => target.value),
    reasons,
  };
}
