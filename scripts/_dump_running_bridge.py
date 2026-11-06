#!/usr/bin/env python3
from pathlib import Path
import os

pid = 2667124
cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode()
print("CMD:", cmdline)
print("--- file on disk ---")
print(Path("/home/bossjy/.local/bin/codex_bridge_minimal.py").read_text())
