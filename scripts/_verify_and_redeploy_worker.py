#!/usr/bin/env python3
import ast
import shutil
import subprocess
from pathlib import Path

src = Path("/mnt/c/Users/Administrator/Desktop/JySecAI/scripts/codex_bridge_worker_v2.py")
dst = Path("/home/bossjy/.local/bin/codex_bridge_worker.py")

src_text = src.read_text(encoding="utf-8")
dst_text = dst.read_text(encoding="utf-8")
print("src lines", src_text.count("\n"), "dst lines", dst_text.count("\n"))
print("dst has sanitize_tools", "def sanitize_tools" in dst_text)
print("dst has write_out", "def write_out" in dst_text)
print("dst has soften", "def soften_for_cyber_policy" in dst_text)

# Always redeploy v2
shutil.copyfile(src, dst)
dst.chmod(0o755)
ast.parse(dst.read_text(encoding="utf-8"))
print("redeployed parse_ok", dst.stat().st_size)

# quick import of key names via compile
ns = {}
# don't exec full (imports hermes); just check defs by parsing
tree = ast.parse(dst.read_text(encoding="utf-8"))
defs = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
need = {"write_out", "sanitize_tools", "soften_for_cyber_policy", "main", "_force_object_schema"}
print("defs", sorted(need & defs))
missing = need - defs
print("missing", missing or "none")
