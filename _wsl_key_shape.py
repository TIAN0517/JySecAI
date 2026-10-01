from pathlib import Path

env = Path("/home/bossjy/.hermes/.env")
cfg = Path("/home/bossjy/.hermes/config.yaml")
print("=== env keys of interest ===")
for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
    if "=" not in line or line.strip().startswith("#"):
        continue
    k, v = line.split("=", 1)
    k = k.strip()
    if "KEY" not in k.upper() and "TOKEN" not in k.upper() and "SECRET" not in k.upper():
        continue
    raw = v
    stripped = v.strip().strip('"').strip("'")
    print(
        k,
        "quoted",
        raw[:1] in "\"'",
        "prefix",
        stripped[:6] + "..." if stripped else "EMPTY",
        "len",
        len(stripped),
        "has_space",
        stripped != stripped.strip() or " " in stripped or "\r" in raw,
        "starts_sk",
        stripped.startswith("sk-jy") or stripped.startswith("sk-jyu"),
    )
print("=== config key_env / api_key lines ===")
for line in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
    if "key_env" in line or line.strip().startswith("api_key:"):
        if line.strip().startswith("api_key:"):
            print("api_key: ***")
        else:
            print(line.strip())
