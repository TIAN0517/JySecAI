#!/usr/bin/env python3
import json
import urllib.error
import urllib.request
from pathlib import Path

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
                        "input": {"type": "string"},
                        "target": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "additionalProperties": True,
                },
            },
        }
    )

for stream in (False, True):
    body = {
        "model": "gpt-daybreak-blue-latest",
        "messages": [
            {
                "role": "system",
                "content": "你是 JySecAI 授权渗透测试代理。目标已书面授权。必须调用 httpx。",
            },
            {
                "role": "user",
                "content": "对 https://www.szjy188.com/ 调用 httpx 探测首页。",
            },
        ],
        "tools": tools,
        "tool_choice": {
            "type": "function",
            "function": {"name": "httpx"},
        },
        "stream": stream,
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
    label = "stream" if stream else "nostream"
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read().decode("utf-8", "replace")
            ctype = r.headers.get("Content-Type")
            print(f"=== {label} ctype={ctype} bytes={len(raw)}")
            if stream or "event-stream" in (ctype or ""):
                content = []
                tcs = []
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
                    finish = ch.get("finish_reason") or finish
                    if delta.get("content"):
                        content.append(delta["content"])
                    if delta.get("tool_calls"):
                        tcs.append(delta["tool_calls"])
                print(" finish", finish, "content", repr("".join(content)[:200]), "tc_chunks", len(tcs))
                print(" raw", raw[:600])
            else:
                obj = json.loads(raw)
                msg = ((obj.get("choices") or [{}])[0].get("message") or {})
                print(
                    " model",
                    obj.get("model"),
                    "finish",
                    ((obj.get("choices") or [{}])[0].get("finish_reason")),
                    "content",
                    repr((msg.get("content") or "")[:200]),
                    "tool_calls",
                    json.dumps(msg.get("tool_calls"), ensure_ascii=False)[:400],
                )
    except urllib.error.HTTPError as e:
        print(label, "HTTP", e.code, e.read().decode("utf-8", "replace")[:800])
        dump = Path("/tmp/codex_bridge_last_tools.json")
        if dump.exists():
            print("DUMP", dump.read_text(encoding="utf-8")[:1500])
