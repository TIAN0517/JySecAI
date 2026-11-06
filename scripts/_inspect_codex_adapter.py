#!/usr/bin/env python3
from pathlib import Path

text = Path("/home/bossjy/.hermes/hermes-agent/agent/auxiliary_client.py").read_text(encoding="utf-8")
idx = text.find("class _CodexCompletionsAdapter")
print(text[idx : idx + 6000])
print("\n\n===== search access nearby =====")
# also search for responses.create patterns with extra_body in this file around Codex
for needle in ("_CodexCompletionsAdapter", "responses.create", "access_program", "cyber"):
    print(needle, text.count(needle))
