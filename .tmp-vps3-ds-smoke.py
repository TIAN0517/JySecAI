from pathlib import Path
import json
import urllib.request
import urllib.error

env = Path("/home/bossjy/.hermes/.env")
k = None
for ln in env.read_text(encoding="utf-8").splitlines():
    if ln.startswith("DEEPSEEK_API_KEY="):
        k = ln.split("=", 1)[1].strip()
        break
body = json.dumps({
    "model": "deepseek/deepseek-v4-pro-0813",
    "messages": [{"role": "user", "content": "只回 ok"}],
    "max_tokens": 8,
    "stream": False,
}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:18790/chat/completions",
    data=body,
    headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read().decode())
    print("status", 200)
    print("used-model", data.get("model"))
    msg = ((data.get("choices") or [{}])[0].get("message") or {})
    print("has-content", bool(msg.get("content") or msg.get("reasoning_content")))
except urllib.error.HTTPError as e:
    print("status", e.code)
    print("err-len", len(e.read() or b""))
except Exception as e:
    print("fail", type(e).__name__)
