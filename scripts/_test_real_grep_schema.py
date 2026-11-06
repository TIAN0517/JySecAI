#!/usr/bin/env python3
import json
import urllib.request
from pathlib import Path

# Exact schema from InferTool dump
tool = {
    "type": "function",
    "function": {
        "description": "search files",
        "name": "grep",
        "parameters": {
            "additionalProperties": False,
            "properties": {
                "-A": {"description": "After lines", "type": "integer"},
                "-B": {"description": "Before lines", "type": "integer"},
                "-C": {"description": "Context lines", "type": "integer"},
                "-i": {"description": "Case insensitive", "type": "boolean"},
                "-n": {"description": "Show line numbers", "type": "boolean"},
                "glob": {"description": "Glob pattern", "type": "string"},
                "head_limit": {"description": "Head limit", "type": "integer"},
                "multiline": {"description": "Multiline", "type": "boolean"},
                "offset": {"description": "Offset", "type": "integer"},
                "output_mode": {
                    "description": "Output mode",
                    "enum": ["content", "files_with_matches", "count"],
                    "type": "string",
                },
                "path": {"description": "File or directory to search in", "type": "string"},
                "pattern": {
                    "description": "The regular expression pattern to search for in file contents",
                    "type": "string",
                },
                "type": {"description": "File type", "type": "string"},
            },
            "required": ["pattern"],
            "type": "object",
        },
    },
}

body = json.dumps(
    {
        "model": "gpt-6-astra",
        "messages": [{"role": "user", "content": "Reply with exactly: PONG. Do not call tools."}],
        "tools": [tool],
        "tool_choice": "none",
    }
).encode()
req = urllib.request.Request(
    "http://127.0.0.1:18787/v1/chat/completions",
    data=body,
    headers={"Authorization": "Bearer jysec-codex-bridge", "Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        print("OK", r.status, r.read()[:500].decode())
except Exception as e:
    print("ERR", e)
    if hasattr(e, "read"):
        print(e.read()[:1000].decode())
    p = Path("/tmp/codex_bridge_last_tools.json")
    if p.exists():
        print(p.read_text(encoding="utf-8")[:5000])
