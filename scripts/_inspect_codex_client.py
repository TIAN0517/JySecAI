#!/usr/bin/env python3
from pathlib import Path
import re

p = Path("/home/bossjy/.hermes/hermes-agent/agent/auxiliary_client.py")
text = p.read_text(encoding="utf-8")
# find _build_codex_client and nearby
for m in re.finditer(r"def _build_codex_client|access_program|extra_body|daybreak|cyber", text):
    print(m.group(), "at", m.start())

idx = text.find("def _build_codex_client")
print("\n=== _build_codex_client ===")
print(text[idx : idx + 3500])

# also search whole hermes for access_programs string in all files
hits = []
for f in Path("/home/bossjy/.hermes").rglob("*"):
    if not f.is_file():
        continue
    if f.suffix.lower() not in {".py", ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".js", ".ts"}:
        continue
    try:
        t = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    if "access_programs" in t:
        hits.append(str(f))
print("\naccess_programs files:", hits[:30])
