import json
from pathlib import Path

p = Path("/home/bossjy/.openclaw/openclaw.json")
data = json.loads(p.read_text(encoding="utf-8"))
prov = ((data.get("models") or {}).get("providers") or {}).get("deepseek") or {}
print("deepseek-provider-keys", sorted(prov.keys()))
for k, v in prov.items():
    if str(k).lower() in {"apikey", "api_key", "key", "token"}:
        print(k, "set", bool(v), "type", type(v).__name__, "len", len(v) if isinstance(v, str) else "")
    elif k == "models":
        print("models-type", type(v).__name__, "len", len(v) if isinstance(v, (list, dict)) else "")
        if isinstance(v, dict):
            print("model-ids", ",".join(list(v.keys())[:30]))
        elif isinstance(v, list):
            for item in v[:20]:
                if isinstance(item, dict):
                    print("model", item.get("id") or item.get("name"), "keys", sorted(item.keys()))
                else:
                    print("model", item)
    else:
        print(k, "=", json.dumps(v, ensure_ascii=False)[:240] if not isinstance(v, (dict, list)) else f"{type(v).__name__}")

defs = (data.get("agents") or {}).get("defaults") or {}
print("defaults.model", defs.get("model"))
print("defaults.models", json.dumps(defs.get("models") or {}, ensure_ascii=False)[:500])
entries = ((data.get("agents") or {}).get("entries") or {}).get("main") or {}
print("main.model", entries.get("model"))
print("main.models", json.dumps(entries.get("models") or {}, ensure_ascii=False)[:500])
