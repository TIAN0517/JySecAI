#!/usr/bin/env python3
"""Forward request access_programs into call_kwargs.extra_body for Daybreak."""
from pathlib import Path

p = Path("/home/bossjy/.local/bin/codex_bridge_worker.py")
text = p.read_text(encoding="utf-8")

# Ensure request-level access_programs / extra_body are forwarded
needle = '        if req.get("reasoning_effort"):\n            call_kwargs["extra_body"] = {"reasoning": {"effort": req["reasoning_effort"]}}'
if "access_programs" in text and "Forward Daybreak" in text:
    print("forward already present")
else:
    insert = '''        # Forward Daybreak / extra_body from the OpenAI-shaped request.
        _eb = {}
        if isinstance(req.get("extra_body"), dict):
            _eb.update(req["extra_body"])
        if isinstance(req.get("access_programs"), dict):
            _eb["access_programs"] = req["access_programs"]
        if req.get("reasoning_effort"):
            _eb.setdefault("reasoning", {})
            if isinstance(_eb["reasoning"], dict):
                _eb["reasoning"] = {**_eb["reasoning"], "effort": req["reasoning_effort"]}
            else:
                _eb["reasoning"] = {"effort": req["reasoning_effort"]}
        if _eb:
            call_kwargs["extra_body"] = _eb'''
    if needle not in text:
        raise SystemExit("reasoning_effort needle missing")
    text = text.replace(needle, insert, 1)
    p.write_text(text, encoding="utf-8")
    print("forward patched", p.stat().st_size)

# Also: when request explicitly sets cyber=omit, honor it over env default.
# Already handled in inject if extra_body reaches kwargs.
print("ok")
