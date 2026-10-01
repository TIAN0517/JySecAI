import re
from pathlib import Path

p = Path(r"C:\Users\Administrator\AppData\Local\hermes\config.yaml")
print("exists", p.exists(), "size", p.stat().st_size if p.exists() else 0)
text = p.read_text(encoding="utf-8")
red = re.sub(r"(?im)^(\s*(api_key|apiKey|token|password|secret)\s*:\s*).+$", r"\1***", text)
red = re.sub(r"sk-jy-[A-Za-z0-9]+", "sk-jy-***", red)
print(red)
print("---ENV---")
envp = Path(r"C:\Users\Administrator\AppData\Local\hermes\.env")
if envp.exists():
    keys = []
    for line in envp.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            keys.append(line.split("=", 1)[0].strip())
    print("env_keys", keys)
else:
    print("no hermes .env")
