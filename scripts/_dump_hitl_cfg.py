#!/usr/bin/env python3
import yaml, json
c = yaml.safe_load(open("/var/lib/jysecai/core/config.yaml", encoding="utf-8"))
hitl = c.get("hitl")
print("hitl present", hitl is not None)
print(json.dumps(hitl, ensure_ascii=False, indent=2, default=str)[:4000])
# also multi_agent / security related defaults
for k in ("tool_guard", "security", "mcp"):
    if k in c:
        v = c[k]
        if isinstance(v, dict):
            print("---", k, list(v.keys())[:30])
            for kk in ("enabled", "mode", "default_mode", "hitl"):
                if kk in v:
                    print(k, kk, v[kk])
