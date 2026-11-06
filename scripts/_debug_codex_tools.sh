#!/usr/bin/env bash
set -u
echo "==== worker sanitize present? ===="
rg -n 'sanitize_tools|_strip_forbidden|residual combinators|Flat / Responses' /home/bossjy/.local/bin/codex_bridge_worker.py | head -40
echo "==== patch worker to dump tools on error ===="
python3 <<'PY'
from pathlib import Path
import time, shutil
p = Path('/home/bossjy/.local/bin/codex_bridge_worker.py')
text = p.read_text(encoding='utf-8')
if 'DUMP_TOOLS_ON_ERR' not in text:
    bak = p.with_suffix(p.suffix + f'.bak-dump-{time.strftime("%Y%m%d-%H%M%S")}')
    shutil.copy2(p, bak)
    needle = 'except Exception as e:\n        traceback.print_exc()\n        write_out(out_path, 502, {"error": {"message": f"codex subscription error: {e}"}})'
    repl = '''except Exception as e:\n        traceback.print_exc()\n        try:\n            dump = {"DUMP_TOOLS_ON_ERR": True, "model": model, "tools": call_kwargs.get("tools"), "raw_tools": req.get("tools")}\n            open("/tmp/codex_bridge_last_tools.json","w",encoding="utf-8").write(__import__("json").dumps(dump, ensure_ascii=False, indent=2)[:500000])\n        except Exception:\n            pass\n        write_out(out_path, 502, {"error": {"message": f"codex subscription error: {e}"}})'''
    if needle not in text:
        raise SystemExit('needle not found')
    p.write_text(text.replace(needle, repl, 1), encoding='utf-8')
    print('patched dump')
else:
    print('dump already present')
PY

# Also check go side for tool schema conversion / oneOf for grep
cd /mnt/c/Users/Administrator/Desktop/JySecAI
rg -n 'oneOf|InfParam|ParamOption|ToOpenAI|tool.*schema|ConvertToOpenAI' internal/multiagent/*.go internal/einomcp/*.go 2>/dev/null | head -40

# Find GrepRequest json tags in module
rg -n 'type GrepRequest|json:"' /home/bossjy/go/pkg/mod/github.com/cloudwego/eino@v0.9.14/adk/filesystem/*.go 2>/dev/null | head -40
rg -n 'Grep|oneOf|InferTool' /home/bossjy/go/pkg/mod/github.com/cloudwego/eino@v0.9.14/adk/middlewares/filesystem/filesystem.go 2>/dev/null | head -50
