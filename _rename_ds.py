from pathlib import Path
import shutil

d = Path(r"C:\Users\Administrator\Desktop\JySecAI")
pairs = [
    (".tmp-ds-alias-proxy.py", "_ds_alias_proxy.py"),
    (".tmp-ds.key", "_ds.key"),
    (".tmp-vps3-ds-0813-apply.py", "_ds_0813_apply.py"),
]
for src, dst in pairs:
    a, b = d / src, d / dst
    if not a.exists():
        raise SystemExit(f"missing {src}")
    shutil.copy2(a, b)
    print("ok", dst, b.stat().st_size)
