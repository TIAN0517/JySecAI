#!/usr/bin/env python3
from pathlib import Path
p = Path("/tmp/codex_bridge_last_tools.json")
print(p.read_text(encoding="utf-8") if p.exists() else "missing")
