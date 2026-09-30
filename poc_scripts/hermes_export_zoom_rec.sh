#!/usr/bin/env bash
# 匯出「推薦買 ZoomEye / DNS 工具介紹」那段紀錄的 session
set -u
cd /home/bossjy/.hermes/hermes-agent || exit 1
OUT=/mnt/c/Users/Administrator/Desktop/JySecAI/tpe119_evidence/hermes_recovery/exports
mkdir -p "$OUT"
PY=./venv/bin/python
for sid in 20260924_164411_6ed7e1 20260924_183058_42ed9b 20260924_175727_f38b72; do
  echo "== $sid =="
  $PY hermes sessions export --session-id "$sid" --format md --no-redact --yes "$OUT" 2>&1 | tail -2
done
echo
ls -la "$OUT" | tail -12
