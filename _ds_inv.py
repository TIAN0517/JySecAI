from pathlib import Path
import json

print("=== hermes env names ===")
henv = Path("/home/bossjy/.hermes/.env")
if henv.exists():
    for ln in henv.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.strip() and not ln.startswith("#") and "=" in ln:
            print("hermes", ln.split("=", 1)[0])
else:
    print("no-hermes-env")

print("=== openclaw.json models/providers (no secrets) ===")
oc = Path("/home/bossjy/.openclaw/openclaw.json")
if oc.exists():
    raw = oc.read_text(encoding="utf-8", errors="replace")
    data = json.loads(raw)
    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                lk = str(k).lower()
                if any(s in lk for s in ("key", "token", "secret", "password", "auth")):
                    print(f"{path}.{k}=<redacted type={type(v).__name__}>")
                    continue
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj[:20]):
                walk(v, f"{path}[{i}]")
        elif isinstance(obj, str) and ("deepseek" in obj.lower() or "model" in path.lower() or "provider" in path.lower() or "base" in path.lower()):
            print(f"{path}={obj[:160]}")
    walk(data)
print("=== openclaw env names ===")
oenv = Path("/home/bossjy/.openclaw/.env")
if oenv.exists():
    for ln in oenv.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.strip() and not ln.startswith("#") and "=" in ln:
            print("openclaw", ln.split("=", 1)[0])
else:
    print("no-openclaw-env")
