import re
from pathlib import Path

needles = ("mcp", "MCP", "工具", "tool", "熔斷", "timeout", "EOF", "失敗", "error", "Error", "fail")
fail = ("fail", "error", "Error", "失敗", "熔斷", "timeout", "EOF", "refused", "canceled", "429", "500")

def show(path, limit=50):
    print("====", path)
    hits = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        low = line.lower()
        if "mcp" not in low and "tool" not in low and "工具" not in line:
            continue
        if not any(x.lower() in low for x in fail):
            continue
        hits.append(line)
    print("count", len(hits))
    for line in hits[-limit:]:
        print(line[:360])
        print("---")

show("/tmp/jysec-core.log")
show("/tmp/hermes-gw.log")
