#!/usr/bin/env bash
# 把「恢復記憶」的一回合灌回被終端關掉的 session（等同 resume 接回來）
set -u
cd /home/bossjy/.hermes/hermes-agent || exit 1
SID=20260924_164411_6ed7e1
PROMPT_FILE=/mnt/c/Users/Administrator/Desktop/JySecAI/tpe119_evidence/hermes_recovery/resume_turn_prompt.txt

sed -i 's/\r$//' "$PROMPT_FILE"

./venv/bin/python hermes \
  --resume "$SID" \
  --in /mnt/c/Users/Administrator/desktop/JySecAI \
  -z "$(cat "$PROMPT_FILE")" \
  --cli
