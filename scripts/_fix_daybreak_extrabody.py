#!/usr/bin/env python3
"""Fix Daybreak inject to use extra_body (SDK rejects top-level access_programs)."""
from pathlib import Path

p = Path("/home/bossjy/.local/bin/codex_bridge_worker.py")
text = p.read_text(encoding="utf-8")
old = '''                    if str(cyber).lower() not in ("", "0", "false", "off", "none", "omit"):
                        ap = resp_kwargs.get("access_programs")
                        if not isinstance(ap, dict):
                            ap = {}
                        ap = {**ap, "cyber": str(cyber)}
                        resp_kwargs["access_programs"] = ap
                    return resp_kwargs, model_name, timeout'''
new = '''                    if str(cyber).lower() not in ("", "0", "false", "off", "none", "omit"):
                        # OpenAI Python SDK rejects top-level access_programs;
                        # extra_body is merged into the wire JSON after transform.
                        extra = resp_kwargs.get("extra_body")
                        if not isinstance(extra, dict):
                            extra = {}
                        ap = extra.get("access_programs")
                        if not isinstance(ap, dict):
                            ap = {}
                        ap = {**ap, "cyber": str(cyber)}
                        resp_kwargs["extra_body"] = {**extra, "access_programs": ap}
                        resp_kwargs.pop("access_programs", None)
                    return resp_kwargs, model_name, timeout'''
if old not in text:
    raise SystemExit("block missing")
p.write_text(text.replace(old, new, 1), encoding="utf-8")
print("fixed", p.stat().st_size)
