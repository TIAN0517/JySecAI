#!/usr/bin/env bash
set -euo pipefail
cd /mnt/c/Users/Administrator/Desktop/JySecAI
python3 - <<'PY'
from pathlib import Path
src = Path('scripts/_dump_grep_schema.go').read_text(encoding='utf-8')
src = src.replace('//go:build ignore\n\n', '')
Path('/tmp/dump_grep_schema.go').write_text(src, encoding='utf-8')
print('wrote', len(src))
PY
go run /tmp/dump_grep_schema.go 2>&1 | tee /tmp/grep_schema_out.txt | head -300
