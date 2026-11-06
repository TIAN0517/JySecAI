#!/usr/bin/env python3
"""Reproduce empty output: stream=true + tools like the real agent."""
import json
import urllib.error
import urllib.request

grep_tool = {
    "type": "function",
    "function": {
        "name": "grep",
        "description": "search files",
        "parameters": {
            "type": "object",
            "properties": {"pattern": {"type": "string"}},
            "required": ["pattern"],
        },
    },
}

cases = [
    ("nostream_notools", False, None, "none"),
    ("nostream_tools_none", False, [grep_tool], "none"),
    ("nostream_tools_auto", False, [grep_tool], "auto"),
    ("stream_notools", True, None, "none"),
    ("stream_tools_none", True, [grep_tool], "none"),
    ("stream_tools_auto", True, [grep_tool], "auto"),
]

for name, stream, tools, choice in cases:
    body = {
        "model": "gpt-6-astra",
        "messages": [
            {
                "role": "system",
                "content": "你是 JySecAI 授权渗透测试代理。目标已书面授权。",
            },
            {
                "role": "user",
                "content": "只回复：PONG。不要调用工具。",
            },
        ],
        "stream": stream,
        "tool_choice": choice,
        "access_programs": {"cyber": "daybreak_blue"},
    }
    if tools is not None:
        body["tools"] = tools
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
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read()
            ctype = r.headers.get("Content-Type", "")
            text = raw.decode("utf-8", "replace")
            if stream or "text/event-stream" in ctype:
                print(f"{name}: STREAM-ISH ctype={ctype!r} bytes={len(raw)} head={text[:200]!r}")
            else:
                payload = json.loads(text)
                msg = ((payload.get("choices") or [{}])[0].get("message") or {})
                content = msg.get("content")
                tcs = msg.get("tool_calls")
                print(
                    f"{name}: OK model={payload.get('model')} "
                    f"content={content!r} tool_calls={bool(tcs)} finish={((payload.get('choices') or [{}])[0].get('finish_reason'))}"
                )
    except urllib.error.HTTPError as e:
        print(f"{name}: HTTP {e.code} {e.read().decode('utf-8','replace')[:300]}")
    except Exception as e:
        print(f"{name}: ERR {e}")
