# -*- coding: utf-8 -*-
"""Parse hermes dump request.body -> conversation, focus on epcr subdomain / zoomeye task."""
import json, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PATH = sys.argv[1] if len(sys.argv) > 1 else (
    r"C:\Users\Administrator\Desktop\JySecAI\tpe119_evidence\hermes_recovery"
    r"\request_dump_20260923_191618_5ded2c_20260928_012143_299004.json"
)
OUT = r"C:\Users\Administrator\Desktop\JySecAI\tpe119_evidence\hermes_recovery\dump_parsed.txt"
data = json.load(open(PATH, encoding="utf-8"))
body = data["request"]["body"]
if isinstance(body, str):
    body = json.loads(body)
msgs = body.get("messages", [])

fh = open(OUT, "w", encoding="utf-8")
def emit(*a):
    print(*a, file=fh)

emit("timestamp:", data.get("timestamp"), "| reason:", data.get("reason"))
emit("model:", body.get("model"), "| messages:", len(msgs))
err = data.get("error") or {}
emit("error:", err.get("type"), err.get("message", "")[:300])

KEYS = ("epcr", "zoomeye", "fofa", "摮?", "subdomain", "蝮??", "taipei", "擃?", "獢?")
for i, m in enumerate(msgs):
    role = m.get("role")
    content = m.get("content")
    if isinstance(content, list):
        parts = []
        for c in content:
            if not isinstance(c, dict):
                parts.append(str(c))
                continue
            t = c.get("type")
            if t == "text":
                parts.append(c.get("text", ""))
            elif t == "thinking":
                parts.append("[think] " + c.get("thinking", ""))
            elif t == "tool_use":
                parts.append("[tool_use %s] %s" % (c.get("name"), json.dumps(c.get("input", {}), ensure_ascii=False)[:600]))
            elif t == "tool_result":
                cc = c.get("content")
                parts.append("[tool_result] " + (json.dumps(cc, ensure_ascii=False)[:600] if not isinstance(cc, str) else cc[:600]))
        txt = "\n".join(parts)
    else:
        txt = str(content)
    low = txt.lower()
    if any(k in low for k in KEYS):
        emit("\n" + "=" * 78)
        emit("[%d] role=%s len=%d" % (i, role, len(txt)))
        emit(txt[:4000])
fh.close()
print("written", OUT)
