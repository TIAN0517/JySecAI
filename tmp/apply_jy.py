import json
import urllib.request
from pathlib import Path

key = Path(r"C:\Users\Administrator\Desktop\JySecAI\data\.jy-gateway.key").read_text(encoding="utf-8").strip()
body = json.dumps(
    {
        "model": "jy-5.3-coder",
        "stream": False,
        "max_tokens": 16,
        "messages": [{"role": "user", "content": "?芸? ok"}],
    }
).encode()
req = urllib.request.Request(
    "https://llm.jytian.cc.cd/api/v1/chat/completions",
    data=body,
    headers={
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    },
)
try:
    with urllib.request.urlopen(req, timeout=45) as r:
        raw = r.read()
        ok = b'"content"' in raw
        print("chat", r.status, "has_content", int(ok), "bytes", len(raw))
except Exception as e:
    print("err", getattr(e, "code", type(e).__name__), str(e)[:80])
