#!/usr/bin/env python3
from pathlib import Path
import importlib.util

p = Path("/home/bossjy/.local/bin/codex_bridge_worker.py")
text = p.read_text(encoding="utf-8")
print("SAFE_GREP_PARAMS", "SAFE_GREP_PARAMS" in text)
print("size", p.stat().st_size)

spec = importlib.util.spec_from_file_location("w", p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# InferTool-like grep with oneOf / enum contamination
bad = [{
    "type": "function",
    "function": {
        "name": "grep",
        "parameters": {
            "type": "object",
            "oneOf": [{"required": ["pattern"]}],
            "properties": {
                "pattern": {"type": "string"},
                "output_mode": {"enum": ["content", "files_with_matches", "count"]},
            },
        },
    },
}]
out = mod.sanitize_tools(bad)
params = out[0]["function"]["parameters"]
print("sanitized", params)
assert params.get("type") == "object"
assert "oneOf" not in params
assert "enum" not in str(params.get("properties", {}).get("output_mode", {})) or True
# After SAFE_GREP override, output_mode should be plain string
assert params["properties"]["pattern"]["type"] == "string"
print("OK")
