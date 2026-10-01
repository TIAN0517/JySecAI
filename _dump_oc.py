from pathlib import Path
ws = Path("/home/bossjy/.openclaw/workspace")
for name in ("IDENTITY.md", "SOUL.md", "USER.md", "DREAMS.md", "AGENTS.md", "BOOTSTRAP.md"):
    p = ws / name
    print("=" * 8, name, "exists", p.exists(), "=" * 8)
    if p.exists():
        print(p.read_text(encoding="utf-8", errors="replace")[:4000])
        print()
