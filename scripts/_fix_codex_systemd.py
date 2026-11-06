#!/usr/bin/env python3
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

unit = Path("/home/bossjy/.config/systemd/user/codex-bridge.service")
text = unit.read_text(encoding="utf-8")
bak = Path(str(unit) + f".bak-{int(time.time())}")
bak.write_text(text, encoding="utf-8")

text2 = text
text2 = text2.replace(
    "Environment=CODEX_BRIDGE_DEFAULT_MODEL=gpt-6-astra",
    "Environment=CODEX_BRIDGE_DEFAULT_MODEL=gpt-daybreak-blue-latest",
)
if "CODEX_BRIDGE_CYBER_ACCESS" not in text2:
    text2 = text2.replace(
        "Environment=CODEX_BRIDGE_DEFAULT_MODEL=gpt-daybreak-blue-latest\n",
        "Environment=CODEX_BRIDGE_DEFAULT_MODEL=gpt-daybreak-blue-latest\n"
        "Environment=CODEX_BRIDGE_CYBER_ACCESS=daybreak_blue\n",
    )
unit.write_text(text2, encoding="utf-8")
print("unit updated; backup", bak)

# kill anything on 18787
ss = subprocess.check_output(["ss", "-ltnp"], text=True, stderr=subprocess.DEVNULL)
for line in ss.splitlines():
    if ":18787" in line and "pid=" in line:
        pid = int(line.split("pid=")[1].split(",")[0].split(")")[0])
        print("killing", pid)
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError as e:
            print("kill err", e)
time.sleep(1)

subprocess.check_call(["systemctl", "--user", "daemon-reload"])
subprocess.check_call(["systemctl", "--user", "restart", "codex-bridge.service"])
time.sleep(1.5)
print(subprocess.check_output(["systemctl", "--user", "status", "codex-bridge.service", "--no-pager"], text=True)[:800])

req = urllib.request.Request(
    "http://127.0.0.1:18787/v1/health",
    headers={"Authorization": "Bearer jysec-codex-bridge"},
)
with urllib.request.urlopen(req, timeout=5) as r:
    print("health", r.read().decode())
