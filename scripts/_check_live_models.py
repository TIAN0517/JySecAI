#!/usr/bin/env python3
from pathlib import Path
import yaml

text = Path("/var/lib/jysecai/core/config.yaml").read_text(encoding="utf-8")
cfg = yaml.safe_load(text)
m = cfg.get("models") or {}
print("default_channel =", m.get("default_channel"))
for k in (
    "rotate_channels",
    "channel_rotate",
    "failover_channels",
    "channel_failover",
    "failover",
    "rotate",
):
    if k in m:
        print(k, "=", m[k])

# print relevant non-secret lines
for line in text.splitlines():
    low = line.lower()
    if any(
        x in low
        for x in (
            "default_channel",
            "rotate",
            "failover",
            "gpt-sub",
            "gpt-daybreak",
            "minimax",
            "18787",
            "name:",
            "base_url",
            "model:",
        )
    ):
        if any(s in low for s in ("api_key", "password", "token", "secret")):
            if ":" in line:
                print(line.split(":", 1)[0] + ": ***")
        else:
            print(line)
