#!/usr/bin/env python3
"""Read live config (via sudo) and find recent Invalid schema / failover lines."""
import subprocess
import sys

def sh(cmd):
    return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)

# config excerpts
cfg = sh("sudo cat /var/lib/jysecai/core/config.yaml")
keys = (
    "default_channel",
    "rotate",
    "failover",
    "gpt-sub",
    "gpt-daybreak",
    "minimax",
    "18787",
    "base_url",
)
print("=== config hits ===")
for line in cfg.splitlines():
    low = line.lower()
    if any(k in low for k in keys) or ("name:" in low and ("gpt" in low or "mini" in low or "claude" in low)):
        if any(s in low for s in ("api_key", "password", "token", "secret")):
            print(line.split(":", 1)[0] + ": ***")
        else:
            print(line)

print("\n=== journal Invalid schema / failover (last 2h) ===")
j = sh(
    "journalctl -u jysec-core --since '2 hours ago' --no-pager -o short-iso 2>/dev/null | "
    "grep -E 'Invalid schema|codex subscription|failover ChatModel|agentic model failover|18787' | tail -60"
)
print(j or "(no matches)")

print("\n=== bridge process ===")
print(sh("ss -ltnp 2>/dev/null | grep 18787 || true"))
print(sh("ps aux 2>/dev/null | grep -E 'codex_bridge|18787' | grep -v grep || true"))
