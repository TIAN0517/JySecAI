from pathlib import Path
import json

home = Path("/home/bossjy/.hermes")
print("home", home, home.is_dir())
cfg = home / "config.yaml"
if cfg.exists():
    for i, ln in enumerate(cfg.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if i <= 20 or any(k in ln for k in ("fallback", "active", "provider:", "default:", "nous", "deepseek")):
            if "sk-" in ln.lower():
                continue
            print(f"cfg{i}:{ln[:160]}")
auth = home / "auth.json"
if auth.exists():
    try:
        data = json.loads(auth.read_text(encoding="utf-8"))
    except Exception as e:
        print("auth-parse", type(e).__name__)
    else:
        print("auth_keys", sorted(data.keys()))
        print("active_provider", data.get("active_provider"))
        print("logged_providers", [k for k, v in (data.get("providers") or {}).items() if isinstance(v, dict)])
print("env_has_jy", any(ln.startswith("HERMES_JY_GATEWAY_API_KEY=") for ln in (home / ".env").read_text(encoding="utf-8", errors="replace").splitlines()) if (home / ".env").exists() else False)
