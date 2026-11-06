#!/usr/bin/env python3
from pathlib import Path

text = Path("/home/bossjy/.hermes/hermes-agent/agent/auxiliary_client.py").read_text(encoding="utf-8")
idx = text.find("class _CodexCompletionsAdapter")
chunk = text[idx : idx + 15000]
# find def create inside
cidx = chunk.find("\n    def create(")
print(chunk[cidx : cidx + 5000])

# Also check transports/codex.py for access_programs / daybreak
p2 = Path("/home/bossjy/.hermes/hermes-agent/agent/transports/codex.py")
t2 = p2.read_text(encoding="utf-8")
print("\n=== transports/codex.py hits ===")
for i, line in enumerate(t2.splitlines(), 1):
    if any(k in line.lower() for k in ("access_program", "daybreak", "cyber", "extra_body")):
        if "cybersecurity" in line.lower() and "risk" in line.lower():
            print(f"{i}: {line[:180]}")
        elif "access_program" in line or "daybreak" in line.lower() or "cyberAccess" in line:
            print(f"{i}: {line[:180]}")
        elif "extra_body" in line and ("access" in line or "daybreak" in line.lower()):
            print(f"{i}: {line[:180]}")

# broader
print("count access_programs in hermes-agent:", sum(1 for _ in Path('/home/bossjy/.hermes/hermes-agent').rglob('*') if _.is_file() and _.suffix=='.py' and 'access_programs' in _.read_text(encoding='utf-8', errors='ignore')))
