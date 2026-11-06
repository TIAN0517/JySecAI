#!/usr/bin/env python3
from pathlib import Path
import re

p = Path("/home/bossjy/.hermes/hermes-agent/agent/transports/codex.py")
text = p.read_text(encoding="utf-8")
idx = text.find("def _sanitize_astra_request_kwargs")
print(text[idx : idx + 2500])

# also build_kwargs for any daybreak
for i, line in enumerate(text.splitlines(), 1):
    if "access" in line.lower() or "daybreak" in line.lower() or "cyber" in line.lower():
        if "cache" in line.lower():
            continue
        print(f"{i}: {line[:200]}")
