#!/usr/bin/env python3
import subprocess
from pathlib import Path

since = "8 minutes ago"
core = subprocess.check_output(
    ["journalctl", "-u", "jysec-core", "--since", since, "--no-pager", "-o", "short-iso"],
    text=True,
)
bridge = subprocess.check_output(
    ["journalctl", "--user-unit", "codex-bridge.service", "--since", since, "--no-pager", "-o", "cat"],
    text=True,
)

needles = (
    "cybersecurity",
    "codex subscription",
    "Daybreak",
    "empty_model",
    "ShouldRetry",
    "failover",
    "skill",
    "502",
    "gpt-",
    "lastSuccessModel",
)
print("=== CORE HITS ===")
hits = [ln for ln in core.splitlines() if any(n in ln for n in needles)]
print("\n".join(hits[-50:]))
print("\n=== BRIDGE TAIL ===")
print("\n".join(bridge.splitlines()[-60:]))
dump = Path("/tmp/codex_bridge_last_tools.json")
if dump.exists():
    print("\n=== DUMP HEAD ===")
    print(dump.read_text(encoding="utf-8")[:2000])
