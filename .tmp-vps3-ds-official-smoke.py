from pathlib import Path
import json
import urllib.request
import urllib.error

env = Path(r"C:\Users\Administrator\AppData\Local\hermes\.env")
k = None
for ln in env.read_text(encoding="utf-8").splitlines():
    if ln.startswith("DEEPSEEK_API_KEY="):
        k = ln.split("=", 1)[1].strip()
        break
if not k:
    raise SystemExit("no-key")
body = json.dumps({
    "model": "deepseek-v4-pro",
    "messages": [{"role": "user", "content": "只回 ok"}],
    "max_tokens": 8,
    "stream": False,
}).encode()
req = urllib.request.Request(
    "https://api.deepseek.com/chat/completions",
    data=body,
    headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read().decode())
    print("official-status", 200)
    print("used-model", data.get("model"))
    msg = ((data.get("choices") or [{}])[0].get("message") or {})
    print("has-text", bool(msg.get("content") or msg.get("reasoning_content")))
except urllib.error.HTTPError as e:
    print("official-status", e.code)
    print("err-len", len(e.read() or b""))
except Exception as e:
    print("official-fail", type(e).__name__)
