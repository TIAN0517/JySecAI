#!/usr/bin/env python3
"""Find recent agent replies mentioning szjy188 or 非侵入."""
import subprocess
from pathlib import Path

out = Path("/tmp/jysec_szjy_hits.txt")
proc = subprocess.run(
    [
        "journalctl",
        "-u",
        "jysec-core",
        "--since",
        "2026-10-27 01:50:00",
        "--no-pager",
        "-o",
        "short-iso",
    ],
    capture_output=True,
    text=True,
)
needles = (
    "szjy188",
    "非侵入",
    "Invalid schema",
    "agentic model failover",
    "failover ChatModel",
    "gpt-sub",
    "gpt-6-astra",
    "批量任務執行失敗",
    "批量任务执行失败",
)
hits = [ln for ln in (proc.stdout or "").splitlines() if any(n in ln for n in needles)]
out.write_text("\n".join(hits[-100:]) + "\n", encoding="utf-8")
print(f"hits={len(hits)}")
print(out.read_text(encoding="utf-8")[-6000:])
