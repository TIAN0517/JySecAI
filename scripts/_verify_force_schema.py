#!/usr/bin/env python3
import importlib.util
from pathlib import Path

p = Path("/home/bossjy/.local/bin/codex_bridge_worker.py")
spec = importlib.util.spec_from_file_location("w", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
schema = {
    "additionalProperties": False,
    "properties": {
        "output_mode": {
            "description": "Output mode",
            "enum": ["content", "files_with_matches", "count"],
            "type": "string",
        },
        "pattern": {"type": "string"},
        "-A": {"type": "integer"},
    },
    "required": ["pattern"],
    "type": "object",
    "oneOf": [{"required": ["pattern"]}],
}
out = m._force_object_schema(schema)
print(out)
assert "oneOf" not in out
assert "enum" not in str(out)
print("force_ok")
