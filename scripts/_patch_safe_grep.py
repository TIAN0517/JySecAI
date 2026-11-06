#!/usr/bin/env python3
from pathlib import Path

p = Path("/home/bossjy/.local/bin/codex_bridge_worker.py")
text = p.read_text(encoding="utf-8")
if "SAFE_GREP_PARAMS" in text:
    print("already patched")
else:
    needle = '        t = copy.deepcopy(tool)\n        fn = t.get("function")'
    insert = '''        t = copy.deepcopy(tool)
        SAFE_GREP_PARAMS = {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "regex pattern"},
                "path": {"type": "string", "description": "file or directory"},
                "glob": {"type": "string"},
                "output_mode": {"type": "string", "description": "content|files_with_matches|count"},
                "case_insensitive": {"type": "boolean"},
                "head_limit": {"type": "integer"},
                "multiline": {"type": "boolean"},
            },
            "required": ["pattern"],
            "additionalProperties": True,
        }
        def _tool_name(obj):
            if isinstance(obj.get("function"), dict) and obj["function"].get("name"):
                return str(obj["function"]["name"])
            return str(obj.get("name") or "")
        if _tool_name(t) == "grep":
            if isinstance(t.get("function"), dict):
                t["function"]["parameters"] = copy.deepcopy(SAFE_GREP_PARAMS)
                t["function"].pop("input_schema", None)
            else:
                t["parameters"] = copy.deepcopy(SAFE_GREP_PARAMS)
                t.pop("input_schema", None)
            cleaned.append(t)
            continue
        fn = t.get("function")'''
    if needle not in text:
        raise SystemExit("needle missing")
    p.write_text(text.replace(needle, insert, 1), encoding="utf-8")
    print("patched", p.stat().st_size)

# quick import check
import importlib.util
spec = importlib.util.spec_from_file_location("w", p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
tools = [{"type":"function","function":{"name":"grep","parameters":{"oneOf":[{"type":"string"}]}}}]
out = mod.sanitize_tools(tools)
print(out[0]["function"]["parameters"])
assert "oneOf" not in str(out)
print("OK")
