#!/usr/bin/env python3
from pathlib import Path

mini = Path("/home/bossjy/.local/bin/codex_bridge_minimal.py").read_text(encoding="utf-8")
work = Path("/home/bossjy/.local/bin/codex_bridge_worker.py").read_text(encoding="utf-8")
print("=== minimal ===")
print(mini)
print("\n=== worker markers ===")
for needle in ("SAFE_GREP_PARAMS", "sanitize_tools", "oneOf", "dump", "Invalid schema"):
    print(needle, needle in work)
# show sanitize_tools function start
idx = work.find("def sanitize_tools")
print("\n=== sanitize_tools excerpt ===")
print(work[idx : idx + 1800] if idx >= 0 else "MISSING")
