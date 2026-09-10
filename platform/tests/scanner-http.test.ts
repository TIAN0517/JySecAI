import { describe, expect, it } from "vitest";

import { matchesNumericDnsSan } from "../src/scanner-adapter/http.js";

describe("scanner adapter TLS compatibility", () => {
  it("accepts only an exact numeric DNS SAN fallback", () => {
    expect(matchesNumericDnsSan("52.128.238.210", "DNS:52.128.238.210")).toBe(true);
    expect(matchesNumericDnsSan("52.128.238.210", "DNS:52.128.238.211")).toBe(false);
    expect(matchesNumericDnsSan("52.128.238.210", "IP Address:52.128.238.210")).toBe(false);
    expect(matchesNumericDnsSan("scanner.example", "DNS:scanner.example")).toBe(false);
  });
});
