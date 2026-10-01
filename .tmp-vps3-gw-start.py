import json
import os
import subprocess
import time
from pathlib import Path

home = Path(r"C:\Users\Administrator\AppData\Local\hermes")
exe = home / "bin" / "hermes.exe"
print("exe", exe.exists())
q = subprocess.run(["schtasks", "/Query", "/TN", "Hermes_Gateway", "/V", "/FO", "LIST"], capture_output=True, text=True, encoding="utf-8", errors="replace")
text = (q.stdout or q.stderr or "")
for ln in text.splitlines():
    low = ln.lower()
    if any(k in low for k in ("task to run", "start in", "status", "last result", "working")):
        print(ln.encode("ascii", "replace").decode("ascii"))

# Start detached via hermes.exe if present
if exe.exists():
    log = home / "gateway.restart.log"
    with log.open("ab") as fh:
        proc = subprocess.Popen(
            [str(exe), "gateway", "run"],
            cwd=str(home),
            stdout=fh,
            stderr=fh,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
        )
    print("spawned", proc.pid)
    time.sleep(8)
else:
    print("no-exe")

pidf = home / "gateway.pid"
if pidf.exists():
    print("pidfile", pidf.read_text(encoding="utf-8", errors="replace")[:220])
net = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, encoding="utf-8", errors="replace")
hits = 0
for ln in (net.stdout or "").splitlines():
    if "LISTENING" in ln and (":18789" in ln or ":18790" in ln):
        print("listen", ln.encode("ascii", "replace").decode("ascii"))
        hits += 1
print("hits", hits)
