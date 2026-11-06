#!/usr/bin/env python3
import subprocess
from pathlib import Path

print("=== recent core ===")
core = subprocess.check_output(
    ["journalctl", "-u", "jysec-core", "--since", "3 minutes ago", "--no-pager", "-o", "cat"],
    text=True,
)
for ln in core.splitlines():
    if any(x in ln for x in ("cybersecurity", "codex subscription", "soften", "502", "failover", "执行失败", "執行失敗")):
        print(ln[:400])

print("\n=== bridge ===")
br = subprocess.check_output(
    ["journalctl", "--user-unit", "codex-bridge.service", "--since", "3 minutes ago", "--no-pager", "-o", "cat"],
    text=True,
)
for ln in br.splitlines()[-40:]:
    print(ln[:300])

dump = Path("/tmp/codex_bridge_last_tools.json")
print("\n=== dump ===")
if dump.exists():
    print(dump.read_text(encoding="utf-8")[:2500])
else:
    print("missing")

w = Path("/home/bossjy/.local/bin/codex_bridge_worker.py").read_text(encoding="utf-8")
print("\n=== worker markers ===")
for n in ("soften_for_cyber_policy", "harder soften", "daybreak cyber inject", "access_programs"):
    print(n, n in w)
