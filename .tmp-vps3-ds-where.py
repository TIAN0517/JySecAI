from pathlib import Path
import json
import subprocess

print("=== windows hermes ===")
wh = Path(r"C:\Users\Administrator\AppData\Local\hermes")
print("win-home", wh.exists())
if wh.exists():
    for name in ("config.yaml", ".env", "auth.json", "gateway.pid"):
        p = wh / name
        print("win", name, p.exists(), p.stat().st_size if p.exists() else 0)
    auth = wh / "auth.json"
    if auth.exists():
        print("win-active", json.loads(auth.read_text(encoding="utf-8")).get("active_provider"))
    env = wh / ".env"
    if env.exists():
        names = []
        for ln in env.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.startswith("DEEPSEEK"):
                names.append(ln.split("=", 1)[0])
        print("win-ds-env", ",".join(names) or "none")
    cfg = wh / "config.yaml"
    if cfg.exists():
        t = cfg.read_text(encoding="utf-8", errors="replace")
        print("win-has-0813-alias", "deepseek/deepseek-v4-pro-0813:" in t)
        print("win-default-line", next((ln.strip() for ln in t.splitlines() if ln.strip().startswith("default:")), ""))

print("=== listen ===")
r = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, encoding="utf-8", errors="replace")
for ln in (r.stdout or "").splitlines():
    if "LISTENING" in ln and any(p in ln for p in (":18789", ":18790", ":18791", ":8646")):
        print(ln)

print("=== pidfile ===")
pidf = wh / "gateway.pid"
if pidf.exists():
    print(pidf.read_text(encoding="utf-8", errors="replace")[:200])
