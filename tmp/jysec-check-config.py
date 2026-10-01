from pathlib import Path
import traceback

p = Path(r"C:\Users\Administrator\Desktop\JySecAI\config.yaml")
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

text = p.read_text(encoding="utf-8", errors="replace")
print("BYTES", p.stat().st_size)
print("HAS_JY", "jy-gateway:" in text)
print("DEFAULT", [ln.strip() for ln in text.splitlines() if "default_channel" in ln][:3])

# 印出 channels 開頭 40 行（遮罩）
lines = text.splitlines()
start = next((i for i, ln in enumerate(lines) if ln.strip() == "channels:" or ln.rstrip().endswith("channels:")), -1)
print("CHANNELS_AT", start + 1)
if start >= 0:
    for i, ln in enumerate(lines[start : start + 40], start=start + 1):
        if "api_key" in ln.lower() or "password" in ln.lower() or "secret" in ln.lower() or "token:" in ln.lower():
            print(f"{i}|***")
        else:
            print(f"{i}|{ln}")

if yaml is None:
    print("NO_PYYAML")
else:
    try:
        yaml.safe_load(text)
        print("YAML_OK")
    except Exception as e:
        print("YAML_ERR", type(e).__name__, str(e)[:400])
        traceback.print_exc()
