import json
import subprocess
import time
from pathlib import Path

time.sleep(8)
pidf = Path(r"C:\Users\Administrator\AppData\Local\hermes\gateway.pid")
if pidf.exists():
    print("pidfile", json.loads(pidf.read_text(encoding="utf-8")).get("pid"))
else:
    print("pidfile missing")
net = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, encoding="utf-8", errors="replace")
hits = 0
for ln in (net.stdout or "").splitlines():
    if "LISTENING" in ln and (":18789" in ln or ":18790" in ln or ":8646" in ln):
        print("listen", ln.encode("ascii", "replace").decode("ascii"))
        hits += 1
print("hits", hits)
tl = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"], capture_output=True, text=True, encoding="utf-8", errors="replace")
print("python-rows", len((tl.stdout or "").splitlines()))
