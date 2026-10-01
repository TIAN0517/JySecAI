import json
import subprocess
import time
from pathlib import Path

pidf = Path(r"C:\Users\Administrator\AppData\Local\hermes\gateway.pid")
old = json.loads(pidf.read_text(encoding="utf-8")) if pidf.exists() else {}
print("pidfile", old.get("kind"), old.get("pid"))

net = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, encoding="utf-8", errors="replace")
owners = []
for ln in (net.stdout or "").splitlines():
    if "LISTENING" in ln and ":18789" in ln:
        print("listen", ln.encode("ascii", "replace").decode("ascii"))
        owners.append(ln.strip().split()[-1])

pids = {str(old.get("pid") or ""), *owners}
pids.discard("")
pids.discard("0")
print("kill-candidates", ",".join(sorted(pids)))
for pid in pids:
    k = subprocess.run(["taskkill", "/PID", pid, "/T", "/F"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = ((k.stdout or "") + (k.stderr or "")).encode("ascii", "replace").decode("ascii")
    print("kill", pid, k.returncode, out[:120])

time.sleep(2)
run = subprocess.run(["schtasks", "/Run", "/TN", "Hermes_Gateway"], capture_output=True, text=True, encoding="utf-8", errors="replace")
rout = ((run.stdout or "") + (run.stderr or "")).encode("ascii", "replace").decode("ascii")
print("run", run.returncode, rout[:120])
time.sleep(6)
if pidf.exists():
    new = json.loads(pidf.read_text(encoding="utf-8"))
    print("new-pidfile", new.get("kind"), new.get("pid"))
else:
    print("new-pidfile missing")
net2 = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, encoding="utf-8", errors="replace")
hits = 0
for ln in (net2.stdout or "").splitlines():
    if "LISTENING" in ln and (":18789" in ln or ":18790" in ln):
        print("after", ln.encode("ascii", "replace").decode("ascii"))
        hits += 1
print("listen-hits", hits)
