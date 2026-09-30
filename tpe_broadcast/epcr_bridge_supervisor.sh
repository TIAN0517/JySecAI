#!/bin/bash
# epcr_bridge_supervisor.sh — Auto-restart wrapper for epcr_tpe_bridge.py
# Runs indefinitely, restarts on crash with 10s delay

BRIDGE_SCRIPT="/mnt/c/Users/Administrator/Desktop/JySecAI/poc_scripts/epcr_tpe_bridge.py"
LOG_FILE="/mnt/c/Users/Administrator/Desktop/JySecAI/tpe_broadcast/data/epcr_bridge.log"
SUPERVISOR_LOG="/mnt/c/Users/Administrator/Desktop/JySecAI/tpe_broadcast/data/epcr_bridge_supervisor.log"
ENVIRONMENT="PYTHONWARNINGS=ignore"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE" "$SUPERVISOR_LOG"

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting epcr_tpe_bridge.py…" >> "$SUPERVISOR_LOG"
    PYTHONWARNINGS=ignore python3 -u "$BRIDGE_SCRIPT" >> "$LOG_FILE" 2>&1
    EXIT_CODE=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bridge exited (code=$EXIT_CODE). Restarting in 10s…" >> "$SUPERVISOR_LOG"
    sleep 10
done
