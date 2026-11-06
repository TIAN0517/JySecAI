#!/usr/bin/env python3
from pathlib import Path

p = Path("/home/bossjy/.hermes/hermes-agent/agent/sdk_transform_bypass.py")
print(p.read_text(encoding="utf-8")[:4000])

# How does main transport pass unknown fields?
t = Path("/home/bossjy/.hermes/hermes-agent/agent/transports/codex.py").read_text(encoding="utf-8")
for i, line in enumerate(t.splitlines(), 1):
    if "extra_body" in line or "bypass_sdk" in line or "request_overrides" in line:
        print(f"{i}: {line[:200]}")
