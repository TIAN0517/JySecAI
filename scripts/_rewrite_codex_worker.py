#!/usr/bin/env python3
"""Rewrite codex_bridge_worker.py with aggressive Codex tool-schema sanitization."""
from __future__ import annotations

import shutil
import time
from pathlib import Path

DEST = Path("/home/bossjy/.local/bin/codex_bridge_worker.py")

CONTENT = r'''#!/usr/bin/env python3
"""One-shot Codex chat worker. Args: <request.json> <response.json>"""
from __future__ import annotations

import copy
import json
import os
import sys
import time
import traceback

ENVSP = "/home/bossjy/.hermes/installs/d8834fbacbd924e3/environments/9814e4aa7a924113a961bbc0d94b521c/venv/lib/python3.14/site-packages"
if ENVSP not in sys.path:
    sys.path.insert(0, ENVSP)
sys.path.insert(0, "/home/bossjy/.hermes/hermes-agent")
os.environ.setdefault("HERMES_DISABLE_LAZY_INSTALLS", "1")
os.environ.setdefault("HERMES_SUPERVISED_CHILD", "1")

DEFAULT = "gpt-6-astra"
_TOP_FORBIDDEN = ("oneOf", "anyOf", "allOf", "enum", "const", "not")
_DUMP = "/tmp/codex_bridge_last_tools.json"


def write_out(path: str, status: int, body: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"status": status, "body": body}, f, ensure_ascii=False)


def _force_object_schema(node):
    """Codex: parameters must be type=object and must not contain forbidden top-level keys."""
    if not isinstance(node, dict):
        return {"type": "object", "properties": {}, "additionalProperties": True}

    # If root is a combinator-only schema, collapse to empty object (still callable).
    if any(k in node for k in _TOP_FORBIDDEN) and node.get("type") != "object":
        # Try to salvage properties from first branch.
        for key in ("oneOf", "anyOf", "allOf"):
            branches = node.get(key)
            if isinstance(branches, list):
                for br in branches:
                    if isinstance(br, dict) and br.get("type") == "object":
                        return _force_object_schema(br)
        return {"type": "object", "properties": {}, "additionalProperties": True}

    out = {}
    for k, v in node.items():
        if k in _TOP_FORBIDDEN:
            continue
        out[k] = v

    if out.get("type") != "object":
        return {"type": "object", "properties": {}, "additionalProperties": True}

    props_in = out.get("properties") if isinstance(out.get("properties"), dict) else {}
    props = {}
    for name, sub in props_in.items():
        if not isinstance(sub, dict):
            props[name] = {"type": "string"}
            continue
        # Nested combinators → degrade to string (Codex is picky).
        if any(k in sub for k in _TOP_FORBIDDEN):
            props[name] = {"type": "string", "description": str(sub.get("description") or name)}
            continue
        cleaned = {kk: vv for kk, vv in sub.items() if kk not in _TOP_FORBIDDEN}
        t = cleaned.get("type")
        if t not in ("string", "number", "integer", "boolean", "array", "object"):
            cleaned["type"] = "string"
        if cleaned["type"] == "object":
            cleaned.setdefault("properties", {})
            cleaned.setdefault("additionalProperties", True)
        if cleaned["type"] == "array" and not isinstance(cleaned.get("items"), dict):
            cleaned["items"] = {"type": "string"}
        # json tags like "-B" are awkward; keep name as-is.
        props[name] = cleaned
    out["properties"] = props
    out["additionalProperties"] = True
    # Drop $schema/$defs/$ref which can reintroduce combinators upstream.
    for k in ("$schema", "$defs", "definitions", "$ref"):
        out.pop(k, None)
    return out


def _set_params(holder: dict, key: str = "parameters") -> None:
    raw = holder.get(key)
    holder[key] = _force_object_schema(raw)


def sanitize_tools(tools):
    if not isinstance(tools, list):
        return None
    cleaned = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        t = copy.deepcopy(tool)
        fn = t.get("function")
        if isinstance(fn, dict):
            _set_params(fn, "parameters")
            if "input_schema" in fn:
                _set_params(fn, "input_schema")
        else:
            # Flat / Responses-style tool object
            if "parameters" in t or t.get("type") == "function" or "name" in t:
                if "parameters" in t or "name" in t:
                    _set_params(t, "parameters") if "parameters" in t else t.setdefault(
                        "parameters",
                        {"type": "object", "properties": {}, "additionalProperties": True},
                    )
                    if "parameters" not in t:
                        t["parameters"] = {
                            "type": "object",
                            "properties": {},
                            "additionalProperties": True,
                        }
                    else:
                        _set_params(t, "parameters")
            if "input_schema" in t:
                _set_params(t, "input_schema")
        # Absolute last resort: if anything forbidden remains in this tool blob, nuke params.
        blob = json.dumps(t, ensure_ascii=False)
        if any(f'"{k}"' in blob for k in _TOP_FORBIDDEN):
            name = ""
            if isinstance(fn, dict):
                name = str(fn.get("name") or "")
                fn["parameters"] = {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True,
                }
                fn.pop("input_schema", None)
            else:
                name = str(t.get("name") or "")
                t["parameters"] = {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True,
                }
                t.pop("input_schema", None)
            print(f"[codex-bridge-worker] nuked residual combinators for tool={name!r}", flush=True)
        cleaned.append(t)
    return cleaned


def serialize_tool_calls(tool_calls):
    if not tool_calls:
        return None
    out = []
    for idx, tc in enumerate(tool_calls):
        fn = getattr(tc, "function", None)
        out.append(
            {
                "index": idx,
                "id": getattr(tc, "id", None) or f"call_{idx}",
                "type": "function",
                "function": {
                    "name": getattr(fn, "name", "") if fn else "",
                    "arguments": getattr(fn, "arguments", "{}") if fn else "{}",
                },
            }
        )
    return out


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: codex_bridge_worker.py <in.json> <out.json>", file=sys.stderr)
        return 2
    in_path, out_path = sys.argv[1], sys.argv[2]
    try:
        with open(in_path, encoding="utf-8") as f:
            req = json.load(f)
    except Exception as e:
        write_out(out_path, 400, {"error": {"message": f"invalid json: {e}"}})
        return 0

    model = (req.get("model") or DEFAULT).strip() or DEFAULT
    if "/" in model:
        model = model.rsplit("/", 1)[-1]
    aliases = {
        "codex-default": DEFAULT,
        "gpt-daybreak-blue-lates": "gpt-daybreak-blue-latest",
        "daybreak": "gpt-daybreak-blue-latest",
        "daybreak-blue": "gpt-daybreak-blue-latest",
        "gpt-daybreak": "gpt-daybreak-blue-latest",
        "gpt-daybreak-blue-latest-900k": "gpt-daybreak-blue-latest",
    }
    model = aliases.get(model, model)
    messages = req.get("messages") or []
    if not messages:
        write_out(out_path, 400, {"error": {"message": "no messages"}})
        return 0

    call_kwargs = {"model": model, "messages": messages}
    try:
        from agent.auxiliary_client import _build_codex_client

        client, _ = _build_codex_client(model)
        if client is None:
            write_out(out_path, 503, {"error": {"message": "ChatGPT subscription credentials unavailable"}})
            return 0
        if req.get("tools"):
            call_kwargs["tools"] = sanitize_tools(req["tools"])
        if req.get("tool_choice") is not None:
            call_kwargs["tool_choice"] = req["tool_choice"]
        if req.get("reasoning_effort"):
            call_kwargs["extra_body"] = {"reasoning": {"effort": req["reasoning_effort"]}}
        resp = client.chat.completions.create(**call_kwargs)
        msg = resp.choices[0].message
        content = getattr(msg, "content", None) or ""
        tool_calls = serialize_tool_calls(getattr(msg, "tool_calls", None))
        finish_reason = getattr(resp.choices[0], "finish_reason", None) or (
            "tool_calls" if tool_calls else "stop"
        )
        usage_obj = getattr(resp, "usage", None)
        message = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        write_out(
            out_path,
            200,
            {
                "id": f"chatcmpl-codex-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": message,
                        "finish_reason": finish_reason,
                    }
                ],
                "usage": {
                    "prompt_tokens": getattr(usage_obj, "prompt_tokens", 0) or 0,
                    "completion_tokens": getattr(usage_obj, "completion_tokens", 0) or 0,
                    "total_tokens": getattr(usage_obj, "total_tokens", 0) or 0,
                },
            },
        )
        return 0
    except SystemExit as e:
        write_out(out_path, 502, {"error": {"message": f"hermes exit: {e}"}})
        return 0
    except Exception as e:
        traceback.print_exc()
        try:
            dump = {
                "error": str(e),
                "model": model,
                "raw_tools_sample": (req.get("tools") or [])[:5],
                "sanitized_tools_sample": (call_kwargs.get("tools") or [])[:5],
                "raw_tool_names": [
                    ((t.get("function") or {}).get("name") if isinstance(t, dict) else None)
                    or (t.get("name") if isinstance(t, dict) else None)
                    for t in (req.get("tools") or [])
                ],
            }
            # Prefer dumping the grep tool fully if present
            for label, arr in (("raw", req.get("tools") or []), ("sanitized", call_kwargs.get("tools") or [])):
                for t in arr:
                    if not isinstance(t, dict):
                        continue
                    name = ((t.get("function") or {}).get("name") if isinstance(t.get("function"), dict) else None) or t.get("name")
                    if name == "grep":
                        dump[f"{label}_grep"] = t
            with open(_DUMP, "w", encoding="utf-8") as f:
                json.dump(dump, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        write_out(out_path, 502, {"error": {"message": f"codex subscription error: {e}"}})
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main() -> None:
    bak = DEST.with_suffix(DEST.suffix + f".bak-rewrite-{time.strftime('%Y%m%d-%H%M%S')}")
    shutil.copy2(DEST, bak)
    print("backup", bak)
    DEST.write_text(CONTENT, encoding="utf-8")
    DEST.chmod(0o755)
    print("wrote", DEST, DEST.stat().st_size)

    # self-test
    import importlib.util

    spec = importlib.util.spec_from_file_location("w", DEST)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    samples = [
        {"type": "function", "function": {"name": "grep", "parameters": {"oneOf": [{"type": "object", "properties": {"pattern": {"type": "string"}}}]}}},
        {"type": "function", "name": "grep", "parameters": {"anyOf": [{"type": "string"}, {"type": "object", "properties": {"q": {"type": "string"}}}]}},
        {"type": "function", "function": {"name": "grep", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "mode": {"enum": ["a", "b"]}}, "oneOf": [{"required": ["pattern"]}]}}},
    ]
    out = mod.sanitize_tools(samples)
    blob = json.dumps(out)
    print(json.dumps(out, indent=2, ensure_ascii=False)[:1500])
    for k in ("oneOf", "anyOf", "allOf"):
        if f'"{k}"' in blob:
            raise SystemExit(f"FAILED residual {k}")
    print("SELFTEST_OK")


if __name__ == "__main__":
    main()
