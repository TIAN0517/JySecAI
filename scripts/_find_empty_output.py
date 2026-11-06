#!/usr/bin/env python3
import subprocess
from pathlib import Path

proc = subprocess.run(
    [
        "journalctl",
        "-u",
        "jysec-core",
        "--since",
        "10 minutes ago",
        "--no-pager",
        "-o",
        "short-iso",
    ],
    capture_output=True,
    text=True,
)
needles = (
    "empty_model_output",
    "ShouldRetry",
    "model output rejected",
    "codex",
    "18787",
    "daybreak",
    "gpt-6-astra",
    "gpt-daybreak",
    "eino_callback_error",
    "stream failed",
    "failover",
)
hits = [ln for ln in (proc.stdout or "").splitlines() if any(n in ln for n in needles)]
Path("/tmp/jysec_empty_hits.txt").write_text("\n".join(hits[-80:]) + "\n", encoding="utf-8")
print(f"hits={len(hits)}")
print("\n".join(hits[-40:]))
