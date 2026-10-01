import json
import os
import urllib.request
from pathlib import Path

envp = Path(r"C:\Users\Administrator\AppData\Local\hermes\.env")
key = ""
for line in envp.read_text(encoding="utf-8").splitlines():
    if line.startswith("HERMES_JY_GATEWAY_API_KEY="):
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
        break
print("key_present", bool(key), "key_prefix", (key[:6] + "...") if key else "NONE")

def req(url, data=None, headers=None):
    h = {"User-Agent": "jy-smoke/1.0"}
    if headers:
        h.update(headers)
    r = urllib.request.Request(url, data=data, headers=h, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(r, timeout=90) as resp:
            body = resp.read()[:500].decode("utf-8", "replace")
            return resp.status, body
    except Exception as e:
        code = getattr(getattr(e, "code", None), "real") if False else getattr(e, "code", 0)
        return code or 0, str(e)[:240]

st, body = req("https://llm.jytian.cc.cd/api/v1/health")
print("HEALTH", st, body[:180].replace("\n", " "))

payload = json.dumps({
    "model": "jy-5.3-coder",
    "stream": False,
    "max_tokens": 16,
    "messages": [{"role": "user", "content": "Reply with only: ok"}],
}).encode()
st, body = req(
    "https://llm.jytian.cc.cd/api/v1/chat/completions",
    data=payload,
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
)
print("CHAT", st, body[:220].replace("\n", " "))

# hermes process
import subprocess
q = subprocess.run(["schtasks", "/Query", "/TN", "Hermes_Gateway", "/FO", "LIST"], capture_output=True, text=True)
print("TASK")
print((q.stdout or q.stderr or "")[:500])
