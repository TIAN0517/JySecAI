#!/usr/bin/env bash
# 檢查 JySecAI 內建 MCP 端點的存取狀態。
# 刻意只用一組無效 token：不碰真實憑證，也能分辨服務走的是哪一條拒絕分支。
#
# 判讀（internal/app/app.go:626-634）：
#   回 "global MCP service access is disabled"  -> allow_global_access=false，這把 token 根本不生效
#   回 {"error":"unauthorized"}                 -> 全域存取有開，但 token 不符
#   回 200 + JSON-RPC 結果                        -> token 正確且全域存取有開
#
# 位置
#   ./check-mcp-access.sh [HOST] [PORT] [標頭名]
#   省略 PORT 時會先讀設定檔 mcp.port，讀不到才用 DEFAULT_PORT。
set -uo pipefail

# 預設 port 的來源：config.yaml 的 mcp.port（目前 6689）。
# 設定檔位置可用 JYSSECAI_CONFIG 覆寫，與其他 scripts 的慣例一致。
CONFIG="${JYSSECAI_CONFIG:-/var/lib/jysecai/core/config.yaml}"
DEFAULT_PORT=6689

config_port() {
  # 只在 mcp: 區塊內取 port，避免誤抓其他區段（例如 server.port）。
  # 讀不到就輸出空字串，由呼叫端退回 DEFAULT_PORT。
  [[ -r "$CONFIG" ]] || return 0
  awk '
    /^mcp:[[:space:]]*$/            { inblock = 1; next }
    inblock && /^[^[:space:]#]/      { exit }   # 離開 mcp: 區塊
    inblock && $1 == "port:"         { print $2; exit }
  ' "$CONFIG"
}

HOST="${1:-127.0.0.1}"
PORT="${2:-$(config_port)}"
PORT="${PORT:-$DEFAULT_PORT}"
HDR="${3:-X-MCP-Token}"
BODY='{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

probe() {
  local label="$1"; shift
  local out code payload
  out=$(curl -sS --max-time 8 -w $'\n%{http_code}' \
        -X POST "http://${HOST}:${PORT}/mcp" \
        -H "$HDR: invalid-probe-token" \
        -H 'Content-Type: application/json' \
        -d "$BODY" 2>&1)
  code=$(printf '%s' "$out" | tail -n1)
  payload=$(printf '%s' "$out" | sed '$d')
  printf '%-22s HTTP %s\n' "$label" "$code"
  printf '  回應: %s\n\n' "$(printf '%s' "$payload" | head -c 300)"
}

echo "目標: http://${HOST}:${PORT}/mcp  (標頭 ${HDR})"
echo

probe "帶無效 token"

out=$(curl -sS --max-time 8 -w $'\n%{http_code}' \
      -X POST "http://${HOST}:${PORT}/mcp" \
      -H 'Content-Type: application/json' \
      -d "$BODY" 2>&1)
printf '%-22s HTTP %s\n' "不帶任何憑證" "$(printf '%s' "$out" | tail -n1)"
printf '  回應: %s\n\n' "$(printf '%s' "$out" | sed '$d' | head -c 300)"

echo "若第一列回應含 'global MCP service access is disabled'，代表 allow_global_access=false："
echo "mcp.auth_header_value 目前是死值，不需要同步任何客戶端，舊值也不存在過。"
