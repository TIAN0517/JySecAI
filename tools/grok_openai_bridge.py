#!/usr/bin/env python3
"""Deprecated shim — use grok_openai_bridge_slim.py.

The Hermes-heavy bridge (import hermes_bootstrap + auxiliary_client) was replaced
by the slim device-code bridge that reads ~/.grok/auth.json (tiered SuperGrok
tokens) and exposes POST /v1/auth/login. Keeping this file only so old docs /
aliases that call grok_openai_bridge.py still land on the working server.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

TARGET = Path(__file__).resolve().with_name("grok_openai_bridge_slim.py")

if __name__ == "__main__":
    print(
        "[grok-bridge] deprecated entrypoint; forwarding to grok_openai_bridge_slim.py",
        flush=True,
    )
    sys.argv[0] = str(TARGET)
    runpy.run_path(str(TARGET), run_name="__main__")
