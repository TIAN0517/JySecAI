#!/usr/bin/env python3
"""Reproduce round-2 cybersecurity flag: prior skill tool result + tools."""
import json
import urllib.error
import urllib.request
from pathlib import Path

skill_blob = """# Web Penetration Skill
对目标进行 SQL注入、XSS、命令执行、文件包含 漏洞利用与 POC 验证。
渗透测试步骤：收集攻击面，构造 payload，验证 exploit 链，记录漏洞。
""" * 40

tools = [
    {
        "type": "function",
        "function": {
            "name": "record_vulnerability",
            "description": "记录发现的漏洞详情。填写 POC、payload、复现步骤、利用影响。",
            "parameters": {
                "type": "object",
                "properties": {
                    "evidence": {"type": "string", "description": "POC / payload 证据"},
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "info"],
                    },
                },
                "required": ["evidence"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "httpx",
            "description": "HTTP 探测",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
]

body = {
    "model": "gpt-daybreak-blue-latest",
    "messages": [
        {
            "role": "system",
            "content": "你是 JySecAI 授权渗透测试代理。目标已书面授权。",
        },
        {"role": "user", "content": "评估 https://www.szjy188.com/"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_skill_1",
                    "type": "function",
                    "function": {"name": "skill", "arguments": "{\"name\":\"web-pentest\"}"},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call_skill_1", "content": skill_blob},
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
try:
    with urllib.request.urlopen(req, timeout=180) as r:
        raw = r.read().decode("utf-8", "replace")
        print("OK", r.status, "bytes", len(raw))
        content = []
        tcs = 0
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
                tcs += 1
        print("finish", finish, "content", repr("".join(content)[:200]), "tc_chunks", tcs)
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode("utf-8", "replace")[:800])
    dump = Path("/tmp/codex_bridge_last_tools.json")
    if dump.exists():
        print("DUMP", dump.read_text(encoding="utf-8")[:600])
