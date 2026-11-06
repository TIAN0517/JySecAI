#!/usr/bin/env python3
from pathlib import Path

text = Path("/home/bossjy/.hermes/hermes-agent/agent/auxiliary_client.py").read_text(encoding="utf-8")
idx = text.find("def _build_codex_client")
# find next def at same indent
chunk = text[idx:]
lines = chunk.splitlines()
out = [lines[0]]
for line in lines[1:]:
    if line.startswith("def ") and not line.startswith("def _"):
        # might still be nested; stop at top-level def
        if not line.startswith(" "):
            break
    if line.startswith("def ") and len(line) - len(line.lstrip()) == 0:
        break
    out.append(line)
    if len(out) > 200:
        break
print("\n".join(out[:200]))

# also search access_programs in site-packages of the venv used by worker
venv_sp = Path(
    "/home/bossjy/.hermes/installs/d8834fbacbd924e3/environments/9814e4aa7a924113a961bbc0d94b521c/venv/lib/python3.14/site-packages"
)
print("\n=== site-packages hits ===")
for p in venv_sp.rglob("*"):
    if not p.is_file():
        continue
    if p.suffix not in {".py", ".md", ".json"}:
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    if "access_programs" in t or "cybersecurity risk" in t:
        print(p)
