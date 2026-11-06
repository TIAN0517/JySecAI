#!/usr/bin/env python3
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

src = Path("/mnt/c/Users/Administrator/Desktop/JySecAI/scripts/codex_bridge_minimal_fixed.py")
dst = Path("/home/bossjy/.local/bin/codex_bridge_minimal.py")
bak = Path(f"/home/bossjy/.local/bin/codex_bridge_minimal.py.bak-before-sse-fix-{int(time.time())}")

bak.write_bytes(dst.read_bytes())
shutil.copyfile(src, dst)
dst.chmod(0o755)
print("deployed", dst, "backup", bak)

# find pid listening on 18787
ss = subprocess.check_output(["ss", "-ltnp"], text=True, stderr=subprocess.DEVNULL)
pid = None
for line in ss.splitlines():
    if ":18787" in line and "pid=" in line:
        # users:(("python",pid=2667124,fd=3))
        part = line.split("pid=")[1]
        pid = int(part.split(",")[0].split(")")[0])
        break
print("old_pid", pid)

# capture env/cmdline for restart
python = "/home/bossjy/.hermes/installs/d8834fbacbd924e3/environments/9814e4aa7a924113a961bbc0d94b521c/venv/bin/python"
script = str(dst)
log = Path("/tmp/codex_bridge_minimal.log")

if pid:
    os.kill(pid, signal.SIGTERM)
    for _ in range(20):
        time.sleep(0.2)
        try:
            os.kill(pid, 0)
        except OSError:
            break
    else:
        os.kill(pid, signal.SIGKILL)
        time.sleep(0.3)
    print("stopped", pid)

# free port check
env = os.environ.copy()
env.setdefault("CODEX_BRIDGE_DEFAULT_MODEL", "gpt-daybreak-blue-latest")
env.setdefault("CODEX_BRIDGE_CYBER_ACCESS", "daybreak_blue")
# keep PYTHONPATH for worker children? parent doesn't need hermes
with open(log, "ab") as lf:
    lf.write(f"\n--- restart {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n".encode())
    proc = subprocess.Popen(
        [python, "-u", script],
        stdout=lf,
        stderr=subprocess.STDOUT,
        env=env,
        start_new_session=True,
    )
print("new_pid", proc.pid)
time.sleep(1.0)
# health
import urllib.request

req = urllib.request.Request(
    "http://127.0.0.1:18787/v1/health",
    headers={"Authorization": "Bearer jysec-codex-bridge"},
)
with urllib.request.urlopen(req, timeout=5) as r:
    print("health", r.read().decode())
