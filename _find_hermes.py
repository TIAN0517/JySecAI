from pathlib import Path

roots = [
    Path(r"C:\Users\Administrator"),
    Path(r"C:\Users\Administrator\Desktop\JySecAI"),
    Path(r"C:\Users\Administrator\.hermes"),
    Path(r"C:\Users\Administrator\AppData\Roaming"),
    Path(r"C:\Users\Administrator\AppData\Local"),
]
needles = ("hermes", "config.yaml", "config.toml", ".hermes")
seen = []
for root in roots:
    if not root.exists():
        print("MISS", root)
        continue
    print("ROOT", root)
    if root.name.lower() in {"roaming", "local"}:
        for p in root.iterdir() if root.is_dir() else []:
            n = p.name.lower()
            if "hermes" in n or "nous" in n:
                print(" ", p)
        continue
    for p in root.rglob("*"):
        if not p.is_file() or p.stat().st_size > 2_000_000:
            continue
        name = p.name.lower()
        if "hermes" in str(p).lower() or name in {"config.yaml", "config.toml", "settings.json"}:
            if any(x in p.parts for x in ("node_modules", ".git", "__pycache__")):
                continue
            rel = str(p)
            if "hermes" in rel.lower() or "jy" in name:
                print("FILE", p, p.stat().st_size)
