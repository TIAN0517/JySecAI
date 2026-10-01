#!/bin/bash
# Auto-restart wrapper for broadcast_daemon.py
# Keeps the daemon running: auto-restarts on crash/disconnect.
# Cleans lock file before each start to handle stale locks.
# Usage: ./start_daemon.sh --interval 10 --city 01 [args...]
# Example: ./start_daemon.sh --tg-bot-token TOKEN --ohca-group-id -100XXX

LOG_FILE="/home/bossjy/.hermes/cache/scratch/broadcast_daemon.log"
mkdir -p "$(dirname "$LOG_FILE")"

echo "[wrapper] Started at $(date)" >> "$LOG_FILE"

while true; do
    rm -f /tmp/broadcast_daemon.lock
    # Kill stale login.py daemon processes from previous runs
    pkill -f "login.py --daemon" 2>/dev/null; true
    python3 -u broadcast_daemon.py "$@" >> "$LOG_FILE" 2>&1
    EXIT_CODE=$?
    echo "[wrapper] Daemon exited (rc=$EXIT_CODE) at $(date), restarting in 5s..." >> "$LOG_FILE"
    sleep 5
done
