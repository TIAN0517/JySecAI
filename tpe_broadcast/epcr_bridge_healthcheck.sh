#!/bin/bash
# epcr_bridge_healthcheck.sh — Check bridge daemon health and log errors
# Run via cron every 60 seconds

SUPERVISOR_LOG="/mnt/c/Users/Administrator/Desktop/JySecAI/tpe_broadcast/data/epcr_bridge_supervisor.log"
BRIDGE_LOG="/mnt/c/Users/Administrator/Desktop/JySecAI/tpe_broadcast/data/epcr_bridge.log"
HEALTH_FILE="/mnt/c/Users/Administrator/Desktop/JySecAI/tpe_broadcast/data/epcr_bridge_health.json"

# Check processes
SUPERVISOR_RUNNING=$(ps aux | grep "epcr_bridge_supervisor" | grep -v grep | wc -l)
BRIDGE_RUNNING=$(ps aux | grep "epcr_tpe_bridge" | grep -v grep | wc -l)

# Check for recent errors in log (last 5 min)
ERRORS=$(grep -i -c "error\|traceback\|exception\|failed\|crash\|segfault\|exit" "$BRIDGE_LOG" 2>/dev/null || echo 0)

# Last cycle timestamp (last line with [Cycle)
LAST_CYCLE=$(grep -oP '\d{2}:\d{2}:\d{2}.*Cycle' "$BRIDGE_LOG" 2>/dev/null | tail -1)

# Write health JSON
cat > "$HEALTH_FILE" << EOF
{
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "supervisor_running": $([ "$SUPERVISOR_RUNNING" -gt 0 ] && echo true || echo false),
  "bridge_running": $([ "$BRIDGE_RUNNING" -gt 0 ] && echo true || echo false),
  "error_count": $ERRORS,
  "last_cycle": "$LAST_CYCLE"
}
EOF

# Quick status to stdout
echo "Supervisor: $SUPERVISOR_RUNNING | Bridge: $BRIDGE_RUNNING | Errors: $ERRORS | Last: $LAST_CYCLE"
