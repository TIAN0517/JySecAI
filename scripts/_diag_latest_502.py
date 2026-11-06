#!/usr/bin/env python3
import subprocess

text = subprocess.check_output(
    [
        "journalctl",
        "-u",
        "jysec-core",
        "--since",
        "5 minutes ago",
        "--no-pager",
        "-o",
        "cat",
    ],
    text=True,
)
for needle in (
    "cybersecurity risk",
    "codex subscription",
    "Daybreak",
    "empty_model_output",
    "failover",
    "gpt-",
):
    pass
lines = [ln for ln in text.splitlines() if "codex subscription" in ln or "cybersecurity" in ln or "Daybreak" in ln or "empty_model" in ln]
print("\n".join(lines[-20:]))

# bridge recent
print("\n=== bridge ===")
b = subprocess.check_output(
    ["journalctl", "--user-unit", "codex-bridge.service", "--since", "5 minutes ago", "--no-pager", "-o", "cat"],
    text=True,
)
print("\n".join(b.splitlines()[-40:]))
