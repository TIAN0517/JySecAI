import json
import subprocess
import time
from pathlib import Path

pidf = Path(r"C:\Users\Administrator\AppData\Local\hermes\gateway.pid")
data = json.loads(pidf.read_text(encoding="utf-8")) if pidf.exists() else {}
print("OLD", data.get("kind"), data.get("pid"))
end = subprocess.run(["schtasks", "/End", "/TN", "Hermes_Gateway"], capture_output=True, text=True)
print("END", end.returncode, (end.stdout or end.stderr or "").strip()[:160])
run = subprocess.run(["schtasks", "/Run", "/TN", "Hermes_Gateway"], capture_output=True, text=True)
print("RUN", run.returncode, (run.stdout or run.stderr or "").strip()[:160])
time.sleep(5)
if pidf.exists():
    new = json.loads(pidf.read_text(encoding="utf-8"))
    print("NEW", new.get("kind"), new.get("pid"))
else:
    print("NEW pidfile missing")
