#!/usr/bin/env python3
from pathlib import Path
import re

text = Path("/home/bossjy/.hermes/hermes-agent/agent/auxiliary_client.py").read_text(encoding="utf-8")

# Find CodexAuxiliaryClient class
for name in ("class CodexAuxiliaryClient", "access_programs", "cyberAccessProgram", "daybreak"):
    print(name, text.find(name))

idx = text.find("class CodexAuxiliaryClient")
print("\n=== class ===")
print(text[idx : idx + 8000])
