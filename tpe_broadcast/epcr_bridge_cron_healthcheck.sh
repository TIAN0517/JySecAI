#!/bin/bash
# epcr_bridge_cron_healthcheck.sh — Cron-based health monitor
# Checks every 120 seconds, alerts on crashes
# Install: crontab -e then add:
# */2 * * * * /mnt/c/Users/Administrator/Desktop/JySecAI/tpe_broadcast/epcr_bridge_cron_healthcheck.sh

BRIDGE_LOG="/mnt/c/Users/Administrator/Desktop/JySecAI/tpe_broadcast/data/epcr_bridge.log"
SUPERVISOR_LOG="/mnt/c/Users/Administrator/Desktop/JySecAI/tpe_broadcast/data/epcr_bridge_supervisor.log"
HEALTH_FILE="/mnt/c/Users/Administrator/Desktop/JySecAI/tpe_broadcast/data/epcr_bridge_health.json"
ALERT_FILE="/mnt/c/Users/Administrator/Desktop/JySecAI/tpe_broadcast/data/epcr_bridge_alert.txt"

# Check processes
BRIDGE_RUNNING=$(ps aux | grep "epcr_tpe_bridge" | grep -v grep | wc -l)
SUPERVISOR_RUNNING=$(ps aux | grep "epcr_bridge_supervisor" | grep -v grep | wc -l)

# Check for crashes in last 2 minutes
CRASHES=$(grep -c "Bridge exited" "$SUPERVISOR_LOG" 2>/dev/null || echo 0)

# Check for errors in last 10 lines of bridge log
RECENT_ERRORS=$(tail -10 "$BRIDGE_LOG" 2>/dev/null | grep -i -c "error\|traceback\|exception\|failed" || echo 0)

# Last cycle
LAST_CYCLE=$(grep -oP '\d{2}:\d{2}:\d{2}….*Cycle \d+' "$BRIDGE_LOG" 2>/dev/null | tail -1 | sed 's/.*\(Cycle.*\)/\1/')

# Write health JSON
cat > "$HEALTH_FILE" << EOF
{
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "bridge_running": $([ "$BRIDGE_RUNNING" -gt 0 ] && echo true || echo false),
  "supervisor_running": $([ "$SUPERVISOR_RUNNING" -gt 0 ] && echo true || echo false),
  "crashes": $CRASHES,
  "recent_errors": $RECENT_ERRORS,
  "last_cycle": "$LAST_CYCLE"
}
EOF

# Alert conditions
if [ "$BRIDGE_RUNNING" -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] CRITICAL: Bridge process not running! Supervisor: $SUPERVISOR_RUNNING" > "$ALERT_FILE"
    exit 1
fi

if [ "$RECENT_ERRORS" -gt 0 ] 2>/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $RECENT_ERRORS errors in recent log" > "$ALERT_FILE"
    exit 1
fi

# All good
echo "OK: bridge=$BRIDGE_RUNNING supervisor=$SUPERVISOR_RUNNING errors=$RECENT_ERRORS cycle=$LAST_CYCLE"
echo "" > "$ALERT_FILE"
