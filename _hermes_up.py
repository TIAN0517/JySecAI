import json
import subprocess
from pathlib import Path

ps = subprocess.run(
    ["powershell", "-NoProfile", "-Command",
     "Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'hermes' } | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json"],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
)
print("PROCS")
print((ps.stdout or ps.stderr or "")[:1500])
st = Path(r"C:\Users\Administrator\AppData\Local\hermes\gateway_state.json")
if st.exists():
    data = json.loads(st.read_text(encoding="utf-8"))
    safe = {k: data.get(k) for k in data if "token" not in k.lower() and "key" not in k.lower()}
    print("STATE", json.dumps(safe, ensure_ascii=False)[:500])
net = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, encoding="utf-8", errors="replace")
hits = [ln for ln in (net.stdout or "").splitlines() if "LISTENING" in ln and (":8646" in ln or ":8787" in ln or ":18789" in ln or ":6688" in ln)]
print("LISTEN")
for ln in hits[:20]:
    print(ln)
