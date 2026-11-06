#!/usr/bin/env bash
set -euo pipefail
# stop previous watchers
pkill -f '_codex_health_tick.py' 2>/dev/null || true
pkill -f 'Loop every 60s: Codex' 2>/dev/null || true
sleep 1
exec bash -lc 'while true; do sleep 60; python3 /mnt/c/Users/Administrator/Desktop/JySecAI/scripts/_codex_health_tick.py; done'
