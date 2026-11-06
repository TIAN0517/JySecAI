#!/usr/bin/env python3
from pathlib import Path
import re

roots = [
    Path("/home/bossjy/.hermes/hermes-agent"),
    Path("/home/bossjy/.hermes/installs"),
    Path("/home/bossjy/.local/bin"),
]
needles = ("access_programs", "cybersecurity risk", "access_programs.cyber", "daybreak")
for root in roots:
    if not root.exists():
        print("missing", root)
        continue
    for p in root.rglob("*.py"):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        hits = [n for n in needles if n in text]
        if hits:
            print(p, "->", hits)
            for n in hits:
                for m in re.finditer(re.escape(n), text):
                    i = m.start()
                    print(" ", text[max(0, i - 80) : i + 120].replace("\n", " "))
                    break
