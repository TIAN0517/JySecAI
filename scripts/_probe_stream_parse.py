#!/usr/bin/env python3
import json
import urllib.request

body = json.dumps(
    {
        "model": "gpt-6-astra",
        "messages": [
            {"role": "system", "content": "你是 JySecAI 授权渗透测试代理。"},
            {"role": "user", "content": "只回复：PONG。不要调用工具。"},
        ],
        "stream": True,
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "httpx",
                    "description": "probe http",
                    "parameters": {
                        "type": "object",
                        "properties": {"url": {"type": "string"}},
                        "required": ["url"],
                    },
                },
            }
        ],
        "tool_choice": "auto",
        "access_programs": {"cyber": "daybreak_blue"},
    },
    ensure_ascii=False,
).encode()
req = urllib.request.Request(
    "http://127.0.0.1:18787/v1/chat/completions",
    data=body,
    headers={
        "Authorization": "Bearer jysec-codex-bridge",
        "Content-Type": "application/json",
    },
)
with urllib.request.urlopen(req, timeout=120) as r:
    raw = r.read().decode("utf-8", "replace")
print("RAW:\n", raw)
print("--- parsed ---")
content = []
tool_calls = []
for line in raw.splitlines():
    if not line.startswith("data: "):
        continue
    data = line[6:].strip()
    if data == "[DONE]":
        print("DONE")
        continue
    obj = json.loads(data)
    ch = (obj.get("choices") or [{}])[0]
    delta = ch.get("delta") or {}
    print("chunk", json.dumps(ch, ensure_ascii=False)[:300])
    if delta.get("content"):
        content.append(delta["content"])
    if delta.get("tool_calls"):
        tool_calls.append(delta["tool_calls"])
print("JOINED_CONTENT", repr("".join(content)))
print("TOOL_CALL_DELTAS", tool_calls)
