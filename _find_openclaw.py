from pathlib import Path
cands = [
    Path.home() / ".openclaw",
    Path("/home/bossjy/.openclaw"),
    Path("/root/.openclaw"),
    Path(r"C:\Users\Administrator\.openclaw"),
    Path(r"C:\Users\Administrator\AppData\Roaming\openclaw"),
]
for p in cands:
    print("==", p, "exists", p.exists())
    if not p.exists():
        continue
    for child in sorted(p.rglob("*")):
        if child.is_file() and child.suffix.lower() in {".md", ".json"}:
            rel = child.relative_to(p)
            if str(rel).count("/") + str(rel).count("\\") > 3:
                continue
            print(" ", rel)
