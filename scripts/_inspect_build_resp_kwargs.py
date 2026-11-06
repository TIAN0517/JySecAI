#!/usr/bin/env python3
from pathlib import Path

text = Path("/home/bossjy/.hermes/hermes-agent/agent/auxiliary_client.py").read_text(encoding="utf-8")
idx = text.find("def _build_responses_kwargs")
# from class _CodexCompletionsAdapter
idx = text.find("class _CodexCompletionsAdapter")
chunk = text[idx:]
# find return of _build_responses_kwargs
start = chunk.find("def _build_responses_kwargs")
end = chunk.find("\n    def create(")
print(chunk[start:end][-4000:])
