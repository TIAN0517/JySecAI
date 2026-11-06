#!/usr/bin/env python3
import importlib.util
import json
import urllib.request
from pathlib import Path

# unit sanitize
spec = importlib.util.spec_from_file_location("w", "/home/bossjy/.local/bin/codex_bridge_worker.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
samples = [
    {"type": "function", "function": {"name": "grep", "parameters": {"oneOf": [{"type": "object", "properties": {"pattern": {"type": "string"}}}]}}},
    {"type": "function", "name": "grep", "parameters": {"anyOf": [{"type": "string"}, {"type": "object", "properties": {"q": {"type": "string"}}}]}},
    {
        "type": "function",
        "function": {
            "name": "grep",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "mode": {"enum": ["a", "b"]},
                    "-B": {"type": "integer"},
                    "type": {"type": "string"},
                },
                "oneOf": [{"required": ["pattern"]}],
            },
        },
    },
]
out = mod.sanitize_tools(samples)
blob = json.dumps(out)
print(json.dumps(out, indent=2, ensure_ascii=False)[:2000])
for k in ("oneOf", "anyOf", "allOf"):
    assert f'"{k}"' not in blob, k
print("SELFTEST_OK")

# live bridge
body = json.dumps(
    {
        "model": "gpt-6-astra",
        "messages": [{"role": "user", "content": "Reply with exactly: PONG. Do not call tools."}],
        "tools": samples,
        "tool_choice": "none",
    }
).encode()
req = urllib.request.Request(
    "http://127.0.0.1:18787/v1/chat/completions",
    data=body,
    headers={"Authorization": "Bearer jysec-codex-bridge", "Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        print("LIVE", r.status, r.read()[:400].decode())
except Exception as e:
    print("LIVE_ERR", e)
    if hasattr(e, "read"):
        print(e.read()[:800].decode())
    dump = Path("/tmp/codex_bridge_last_tools.json")
    if dump.exists():
        print(dump.read_text(encoding="utf-8")[:4000])
