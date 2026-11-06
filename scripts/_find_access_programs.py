#!/usr/bin/env python3
from pathlib import Path

root = Path("/home/bossjy/.hermes/hermes-agent")
for p in root.rglob("*"):
    if p.suffix not in {".py", ".md", ".json", ".yml", ".yaml", ".toml"}:
        continue
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    if "access_program" in text or "trusted access for cyber" in text or "cyber parameter" in text:
        print("===", p)
        for i, line in enumerate(text.splitlines(), 1):
            if any(
                k in line
                for k in (
                    "access_program",
                    "trusted access",
                    "cyber parameter",
                    "cybersecurity risk",
                    "DAYBREAK",
                    "extra_body",
                    "safety",
                )
            ):
                print(f"{i}: {line[:200]}")
