#!/usr/bin/env bash
# Copy JySecAI source skills + mcp-servers onto the live release, then merge
# missing external MCP entries into the production config.yaml.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SKILLS_SRC="$ROOT/skills"
MCP_SRC="$ROOT/mcp-servers"
JSON="$ROOT/deploy/arsenal/external-mcp.json"
LIVE_CURRENT="${JYSECAI_CURRENT:-/opt/jysecai/core/current}"
LIVE_CFG="${JYSECAI_CONFIG:-/var/lib/jysecai/core/config.yaml}"
LIVE_SKILLS="$LIVE_CURRENT/skills"
LIVE_MCP="$LIVE_CURRENT/mcp-servers"
SERVICE="${JYSECAI_SERVICE:-jysec-core}"

need_sudo() {
  if [ "$(id -u)" = 0 ]; then
    return 1
  fi
  if sudo -n true 2>/dev/null; then
    return 1
  fi
  return 0
}

run() {
  if [ "$(id -u)" = 0 ]; then
    "$@"
  else
    sudo "$@"
  fi
}

echo "== arsenal sync =="
echo "  skills : $SKILLS_SRC -> $LIVE_SKILLS"
echo "  mcp    : $MCP_SRC -> $LIVE_MCP"
echo "  config : $LIVE_CFG"
echo "  json   : $JSON"

if need_sudo; then
  cat <<EOF

[need sudo] 线上目录属于 jysec，当前 shell 没有免密 sudo。
用管理员执行：

  sudo bash $0

或先：

  sudo rsync -a --delete --exclude '.eino/' "$SKILLS_SRC/" "$LIVE_SKILLS/"
  sudo rsync -a "$MCP_SRC/" "$LIVE_MCP/"
  sudo chown -R jysec:jysec "$LIVE_SKILLS" "$LIVE_MCP"
  sudo python3 $ROOT/deploy/arsenal/merge-mcp-into-config.py --config "$LIVE_CFG" --json "$JSON"
  sudo systemctl restart $SERVICE
EOF
  exit 2
fi

[ -d "$SKILLS_SRC" ] || { echo "missing $SKILLS_SRC" >&2; exit 2; }
[ -f "$JSON" ] || { echo "missing $JSON" >&2; exit 2; }
[ -f "$LIVE_CFG" ] || { echo "missing $LIVE_CFG" >&2; exit 2; }

run mkdir -p "$LIVE_SKILLS" "$LIVE_MCP"
run rsync -a --exclude '.eino/' "$SKILLS_SRC/" "$LIVE_SKILLS/"
run rsync -a "$MCP_SRC/" "$LIVE_MCP/"
run chown -R jysec:jysec "$LIVE_SKILLS" "$LIVE_MCP"
run python3 "$ROOT/deploy/arsenal/merge-mcp-into-config.py" --config "$LIVE_CFG" --json "$JSON"
run systemctl restart "$SERVICE"
echo "[ok] live skills=$(run bash -c "ls -1 '$LIVE_SKILLS' | wc -l")  service=$(run systemctl is-active "$SERVICE")"
