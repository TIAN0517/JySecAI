#!/usr/bin/env bash
# 匯出指定 hermes session（含中斷/未完成的主 session）
set -u
cd /home/bossjy/.hermes/hermes-agent || exit 1
OUT=/mnt/c/Users/Administrator/Desktop/JySecAI/tpe119_evidence/hermes_recovery/exports
mkdir -p "$OUT"
PY=./venv/bin/python

for sid in \
  20260923_191618_5ded2c \
  20260923_191541_b7562e \
  20260928_003351_282501 \
  20260928_010931_309da2 \
  20260928_012824_93fead
do
  echo "== $sid =="
  $PY hermes sessions export --session-id "$sid" --format md --no-redact --yes "$OUT" 2>&1 | tail -2
done
echo
ls -la "$OUT"

