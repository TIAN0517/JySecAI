#!/usr/bin/env python3
import json
import os
import subprocess
from pathlib import Path

pid = subprocess.check_output(
    ["systemctl", "--user", "show", "-p", "MainPID", "--value", "codex-bridge.service"],
    text=True,
).strip()
print("pid", pid)
env = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
for e in env:
    if b"CODEX" in e or b"CYBER" in e:
        print(e.decode(errors="replace"))

dump = Path("/tmp/codex_bridge_last_tools.json")
print("dump exists", dump.exists())
if dump.exists():
    print(dump.read_text(encoding="utf-8")[:2500])

# verify inject code present
w = Path("/home/bossjy/.local/bin/codex_bridge_worker.py").read_text(encoding="utf-8")
print("has inject", "daybreak cyber inject armed" in w)
print("has extra_body access_programs", "access_programs" in w and "extra_body" in w)
