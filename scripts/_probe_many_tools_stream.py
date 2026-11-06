#!/usr/bin/env python3
"""Simulate agent-sized tool list + stream; check if content/tool_calls survive."""
import json
import urllib.request

# Build ~40 tools similar to agent surface
tools = []
for name in [
    "grep", "read_file", "write_file", "glob", "execute", "httpx", "nmap",
    "nuclei", "ffuf", "katana", "subfinder", "dnsx", "wafw00f", "dalfox",
    "search_knowledge_base", "list_vulnerabilities", "record_vulnerability",
    "upsert_project_fact", "query_assets", "create_asset", "batch_task_create",
]:
    tools.append(
        {
            "type": "function",
            "function": {
                "name": name,
                "description": f"tool {name} for authorized security testing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string", "description": "primary input"},
                        "target": {"type": "string"},
                        "path": {"type": "string"},
                        "pattern": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "additionalProperties": True,
                },
            },
        }
    )

body = {
    "model": "gpt-6-astra",
    "messages": [
        {
            "role": "system",
            "content": "你是 JySecAI 授权渗透测试代理。目标已书面授权。优先调用工具。",
        },
        {
            "role": "user",
            "content": "对 https://www.szjy188.com/ 做安全评估，先调用 httpx 探测首页。",
        },
    ],
    "tools": tools,
    "tool_choice": "auto",
    "stream": True,
    "access_programs": {"cyber": "daybreak_blue"},
}

data = json.dumps(body, ensure_ascii=False).encode()
req = urllib.request.Request(
    "http://127.0.0.1:18787/v1/chat/completions",
    data=data,
    headers={
        "Authorization": "Bearer jysec-codex-bridge",
        "Content-Type": "application/json",
    },
)
with urllib.request.urlopen(req, timeout=180) as r:
    raw = r.read().decode("utf-8", "replace")
    ctype = r.headers.get("Content-Type")
print("ctype", ctype, "bytes", len(raw))
content = []
tool_parts = []
finish = None
for line in raw.splitlines():
    if not line.startswith("data: "):
        continue
    payload = line[6:].strip()
    if payload == "[DONE]":
        break
    obj = json.loads(payload)
    ch = (obj.get("choices") or [{}])[0]
    delta = ch.get("delta") or {}
    if ch.get("finish_reason"):
        finish = ch["finish_reason"]
    if delta.get("content"):
        content.append(delta["content"])
    if delta.get("tool_calls"):
        tool_parts.append(delta["tool_calls"])
    # also non-stream full message shape
    msg = ch.get("message")
    if isinstance(msg, dict):
        print("FULL_MESSAGE", json.dumps(msg, ensure_ascii=False)[:500])
print("FINISH", finish)
print("CONTENT", repr("".join(content)[:500]))
print("TOOL_DELTAS_N", len(tool_parts))
if tool_parts:
    print("TOOL0", json.dumps(tool_parts[0], ensure_ascii=False)[:500])
print("RAW_HEAD", raw[:800])
