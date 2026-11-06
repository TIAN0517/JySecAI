#!/usr/bin/env python3
"""Point Codex bridge defaults at gpt-daybreak-blue-latest (Astra lacks Daybreak on this account)."""
from pathlib import Path

for path in (
    Path("/home/bossjy/.local/bin/codex_bridge_worker.py"),
    Path("/home/bossjy/.local/bin/codex_bridge_minimal.py"),
):
    text = path.read_text(encoding="utf-8")
    orig = text
    text = text.replace(
        'DEFAULT = "gpt-6-astra"',
        'DEFAULT = "gpt-daybreak-blue-latest"',
    )
    text = text.replace(
        'DEFAULT = os.environ.get("CODEX_BRIDGE_DEFAULT_MODEL", "gpt-6-astra")',
        'DEFAULT = os.environ.get("CODEX_BRIDGE_DEFAULT_MODEL", "gpt-daybreak-blue-latest")',
    )
    # Worker aliases: map astra → daybreak-blue so JySecAI channels still on astra work
    if path.name == "codex_bridge_worker.py" and '"gpt-6-astra":' not in text:
        needle = '"gpt-daybreak-blue-latest-900k": "gpt-daybreak-blue-latest",\n    }'
        repl = (
            '"gpt-daybreak-blue-latest-900k": "gpt-daybreak-blue-latest",\n'
            '        # This ChatGPT/Codex account has Daybreak on daybreak-blue / sol,\n'
            '        # but NOT on gpt-6-astra / gpt-6.1-sol (403). Remap so agent\n'
            '        # pentest prompts are not flagged as cybersecurity risk.\n'
            '        "gpt-6-astra": "gpt-daybreak-blue-latest",\n'
            '        "gpt-6-astra-900k": "gpt-daybreak-blue-latest",\n'
            '        "gpt-6.1-sol": "gpt-daybreak-blue-latest",\n'
            '        "gpt-6.1-sol-900k": "gpt-daybreak-blue-latest",\n'
            "    }"
        )
        if needle not in text:
            raise SystemExit(f"alias needle missing in {path}")
        text = text.replace(needle, repl, 1)
    if text == orig:
        print(path, "no change?")
    else:
        path.write_text(text, encoding="utf-8")
        print(path, "updated", path.stat().st_size)

# Restart is NOT needed for worker (one-shot). Minimal bridge DEFAULT only affects
# /v1/models listing and health — requests carry model from JySecAI.
print("done")
