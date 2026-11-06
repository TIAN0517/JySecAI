#!/usr/bin/env python3
"""Extract recent schema / failover lines without dumping the whole journal."""
import subprocess
from pathlib import Path

out = Path("/tmp/jysec_journal_hits.txt")
cmd = [
    "journalctl",
    "-u",
    "jysec-core",
    "--since",
    "2026-10-27 01:30:00",
    "--no-pager",
    "-o",
    "short-iso",
]
proc = subprocess.run(cmd, capture_output=True, text=True)
needles = (
    "Invalid schema",
    "codex subscription",
    "failover ChatModel",
    "agentic model failover",
    "schema must have type",
    "gpt-sub",
    "18787",
)
hits = []
for line in (proc.stdout or "").splitlines():
    if any(n in line for n in needles):
        hits.append(line)
out.write_text("\n".join(hits[-80:]) + "\n", encoding="utf-8")
print(f"wrote {len(hits)} hits to {out}")
print(out.read_text(encoding="utf-8")[-4000:])

import os
core = Path("/var/lib/jysecai/core")
print("=== config files ===")
for p in sorted(core.glob("config.yaml*")):
    print(p.name, oct(p.stat().st_mode), p.stat().st_size, "r" if os.access(p, os.R_OK) else "-")
