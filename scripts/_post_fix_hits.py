#!/usr/bin/env python3
import subprocess

text = subprocess.check_output(
    [
        "journalctl",
        "-u",
        "jysec-core",
        "--since",
        "2026-10-27 02:57:30",
        "--no-pager",
        "-o",
        "short-iso",
    ],
    text=True,
)
ns = (
    "cybersecurity",
    "empty_model",
    "ShouldRetry",
    "failover",
    "单代理執行失敗",
    "批量任務執行失敗",
)
lines = [l for l in text.splitlines() if any(n in l for n in ns)]
print("post_fix_hits", len(lines))
print("\n".join(lines[-10:]) if lines else "none")
