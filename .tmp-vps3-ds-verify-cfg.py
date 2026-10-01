from pathlib import Path
import json

home = Path(r"C:\Users\Administrator\AppData\Local\hermes")
cfg = (home / "config.yaml").read_text(encoding="utf-8", errors="replace")
print("has-0813-alias", "deepseek/deepseek-v4-pro-0813:" in cfg)
print("has-official", "api.deepseek.com" in cfg)
print("has-18790-deepseek", "18790" in cfg and "deepseek" in cfg.lower())
for i, ln in enumerate(cfg.splitlines()[:12], 1):
    if any(x in ln for x in ("default:", "provider:", "base_url:")):
        print(f"top{i}", ln.strip())
auth = json.loads((home / "auth.json").read_text(encoding="utf-8"))
print("active_provider", auth.get("active_provider"))
names = []
for ln in (home / ".env").read_text(encoding="utf-8").splitlines():
    if ln.startswith("DEEPSEEK"):
        names.append(ln.split("=", 1)[0])
print("ds-env", ",".join(names))
