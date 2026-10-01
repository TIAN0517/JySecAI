from __future__ import annotations

import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

HERMES = Path(r"C:\Users\Administrator\AppData\Local\hermes")
CFG = HERMES / "config.yaml"
bak = HERMES / f"config.yaml.bak-before-jy-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
shutil.copy2(CFG, bak)
text = CFG.read_text(encoding="utf-8")
pat = re.compile(r"(?ms)^model:\n(?:  .+\n)+")
new = (
    "model:\n"
    "  default: jy-5.3-coder\n"
    "  provider: custom\n"
    "  base_url: https://llm.jytian.cc.cd/api/v1\n"
    "  context_length: 64000\n"
)
if not pat.search(text):
    raise SystemExit("no model block")
CFG.write_text(pat.sub(new, text, count=1), encoding="utf-8")
shown = re.sub(r"(?im)^(\s*(api_key|apiKey|token|password|secret)\s*:\s*).+$", r"\1***", CFG.read_text(encoding="utf-8"))
m = re.search(r"(?ms)^model:\n(?:  .+\n)+", shown)
print("BACKUP", bak.name)
print("MODEL")
print(m.group(0) if m else "missing")
print("HAS_JY_CUSTOM", "llm.jytian.cc.cd" in shown and "jy-5.3-coder" in shown)

subprocess.run(["schtasks", "/End", "/TN", "Hermes_Gateway"], capture_output=True)
run = subprocess.run(["schtasks", "/Run", "/TN", "Hermes_Gateway"], capture_output=True, text=True)
print("TASK_RUN", run.returncode, (run.stdout or run.stderr or "").strip()[:200])
