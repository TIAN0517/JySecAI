from pathlib import Path

cands = [
    Path(r"C:\Users\Administrator\.hermes"),
    Path(r"C:\Users\Administrator\.local\share\hermes"),
    Path(r"C:\Users\Administrator\.local\state\hermes"),
    Path(r"C:\Users\Administrator\.config\hermes"),
    Path(r"C:\Users\Administrator\AppData\Roaming\hermes"),
    Path(r"C:\Users\Administrator\AppData\Local\hermes"),
    Path(r"C:\Users\Administrator\Desktop\JySecAI"),
]
for p in cands:
    print("====", p, "exists" if p.exists() else "MISS")
    if not p.exists():
        continue
    if p.name == "JySecAI":
        for f in p.iterdir():
            n = f.name.lower()
            if "hermes" in n or n in {"config.yaml", "config.yml", "config.toml"}:
                print(" ", f)
        continue
    for f in p.rglob("*"):
        if f.is_file() and f.stat().st_size < 5_000_000:
            if f.suffix.lower() in {".yaml", ".yml", ".toml", ".json", ".md"} or "config" in f.name.lower():
                print(" ", f, f.stat().st_size)
