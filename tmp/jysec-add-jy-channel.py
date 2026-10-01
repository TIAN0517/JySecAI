# 只在 vps3 的 config.yaml 加 jy-gateway，不改 default_channel。
from pathlib import Path
import re
import shutil
from datetime import datetime

cfg_path = Path(r"C:\Users\Administrator\Desktop\JySecAI\config.yaml")
text = cfg_path.read_text(encoding="utf-8", errors="replace")
if re.search(r"(?m)^\s*jy-gateway\s*:", text):
    print("ALREADY_PRESENT")
    raise SystemExit(0)

m = re.search(r"(?m)^(?P<indent>[ \t]*)channels\s*:\s*$", text)
if not m:
    print("NO_CHANNELS_BLOCK")
    raise SystemExit(2)

indent = m.group("indent")
child = indent + "  "
grandchild = indent + "    "
block = (
    f"{child}jy-gateway:\n"
    f"{grandchild}name: Jy Gateway 5.3 Coder\n"
    f"{grandchild}provider: openai_compatible\n"
    f"{grandchild}base_url: https://llm.jytian.cc.cd/api/v1\n"
    f"{grandchild}api_key: \"${{JY_API_KEY}}\"\n"
    f"{grandchild}model: jy-5.3-coder\n"
    f"{grandchild}max_total_tokens: 32768\n"
    f"{grandchild}max_completion_tokens: 8192\n"
    f"{grandchild}reasoning:\n"
    f"{grandchild}  mode: off\n"
)

# 插在 channels: 下一行（與既有 nvidia-primary 並列，不動預設）
insert_at = m.end()
if insert_at < len(text) and text[insert_at] != "\n":
    pass
new_text = text[: insert_at] + "\n" + block + text[insert_at:].lstrip("\n")
if not new_text.endswith("\n"):
    new_text += "\n"

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = cfg_path.with_name(f"config.yaml.bak-jy-{stamp}")
shutil.copy2(cfg_path, backup)
cfg_path.write_text(new_text, encoding="utf-8", newline="\n")
print("INSERTED")
print("BACKUP", backup.name)
print("DEFAULT_UNCHANGED", bool(re.search(r"(?m)^\s*default_channel:\s*nvidia-primary\s*$", new_text)))
