#!/usr/bin/env bash
# 一次完成兩件事：把 jysec-core 的 Web 埠對齊回 8080，並把工作區的修正版核心上線。
#
# 為什麼需要這支
#   2026-11-01 實際發生：
#   1) prod 的 /var/lib/jysecai/core/config.yaml 裡 server.port 漂成 9898，
#      但所有消費端仍以 8080 為準：
#        - /usr/local/sbin/jysec-mcp-watchdog：check_http_restart jysec-core http://127.0.0.1:8080/
#        - /home/bossjy/.local/bin/jysec-stack-guard.py：PROBES core → http://127.0.0.1:8080/
#        - /etc/systemd/system/jysec-edge.service：上游 8080
#        - Windows portproxy：127.0.0.1 8855 → 127.0.0.1 8080
#      結果 watchdog 每 5 分鐘判定核心「掛了」就重啟一次，連帶把外部 MCP 伺服器
#      全部拉掉重建；公開入口（edge）則回 503 service_restarting。
#   2) 同時要上線 internal/handler/hitl_audit_agent.go 的修正：
#      審計 Agent 把 max_completion_tokens 寫死 1024，會思考的模型
#      （MiniMax-M3.1 系列）思考 token 吃光額度 → 決策 JSON 被截斷 →
#      解析失敗 → fail-closed 拒絕，把 nmap/sqlmap/execute 全擋掉。
#
# 核心保證
#   1. 先驗 sha256（source == sidecar），不符就中止。
#   2. 設定檔與二進位都先備份（帶時間戳），失敗可回滾。
#   3. 埠位只改 server: 區塊裡的 port 一行，其他設定一律不動。
#   4. 二進位用 install + mv 原子替換，並保留可執行位元。
#   5. 部署後主動驗證：Web 埠、平台 MCP（6689）工具數、以及 watchdog 的健康探測。
#
# 用法
#   sudo bash scripts/align-port-and-deploy-core.sh
set -uo pipefail

SRC_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="${JYSSECAI_CONFIG:-/var/lib/jysecai/core/config.yaml}"
CURRENT=/opt/jysecai/core/current
TARGET="$CURRENT/jysec-core"
BIN="$SRC_ROOT/jysec-core-linux"
SIDECAR="$BIN.sha256"
SERVICE=jysec-core
MCP_PORT=6689
WANT_PORT=9898
STAMP="$(date +%Y%m%d-%H%M%S)"

step() { printf '\n== %s ==\n' "$*"; }
ok()   { printf '  [OK] %s\n' "$*"; }
bad()  { printf '  [!!] %s\n' "$*"; }
die()  { printf '\n[abort] %s\n' "$*" >&2; exit 2; }

[ "$(id -u)" = "0" ] || die "請用 root 執行：sudo bash $0"
[ -f "$CONFIG" ] || die "找不到設定檔：$CONFIG"
[ -f "$BIN" ] || die "找不到建置產物：$BIN（先 CGO_ENABLED=1 go build -o jysec-core-linux ./cmd/server）"
[ -f "$SIDECAR" ] || die "找不到 sidecar：$SIDECAR（sha256sum jysec-core-linux > jysec-core-linux.sha256）"
[ -f "$TARGET" ] || die "找不到落地檔：$TARGET"

# ───────────────────────────────────────────── 1/6 驗證來源
step "1/6 驗證建置產物"
EXPECT="$(awk 'NF{print $1; exit}' "$SIDECAR")"
ACTUAL="$(sha256sum "$BIN" | awk '{print $1}')"
printf '  sidecar : %s\n  source  : %s\n' "$EXPECT" "$ACTUAL"
[ "$EXPECT" = "$ACTUAL" ] || die "來源與 sidecar 不符（建置後被重新編譯過？）"
ok "source == sidecar"

# ───────────────────────────────────────────── 2/6 備份
step "2/6 備份"
CONFIG_BAK="${CONFIG}.bak-${STAMP}"
BIN_BAK="${TARGET}.bak-${STAMP}"
cp -p "$CONFIG" "$CONFIG_BAK" && ok "設定檔備份 → $CONFIG_BAK"
cp -p "$TARGET" "$BIN_BAK" && ok "二進位備份 → $BIN_BAK"

# ───────────────────────────────────────────── 3/6 埠位對齊
step "3/6 把 server.port 對齊回 $WANT_PORT"
OLD_PORT="$(awk '
  /^server:[[:space:]]*$/ { s=1; next }
  s && /^[^[:space:]#]/       { s=0 }
  s && $1 == "port:"          { gsub(/[^0-9]/,"",$2); print $2; exit }
' "$CONFIG")"
printf '  目前 server.port = %s\n' "${OLD_PORT:-<讀不到>}"
if [ "$OLD_PORT" = "$WANT_PORT" ]; then
  ok "已經是 $WANT_PORT，不需修改"
elif [ -z "$OLD_PORT" ]; then
  die "設定檔的 server: 區塊讀不到 port，請人工確認後再跑"
else
  python3 - "$CONFIG" "$WANT_PORT" <<'PY'
import re, sys
path, want = sys.argv[1], int(sys.argv[2])
lines = open(path, encoding="utf-8").read().splitlines(keepends=True)
in_server = False
changed = False
for i, line in enumerate(lines):
    if re.match(r'^server:\s*$', line):
        in_server = True
        continue
    if in_server and re.match(r'^[^ \t#]', line):
        break
    if in_server and re.match(r'^[ \t]+port:\s*["\']?\d+', line):
        new = re.sub(r'([ \t]+port:\s*["\']?)\d+', lambda m: m.group(1) + str(want), line, count=1)
        lines[i] = new
        changed = True
        break
if not changed:
    sys.exit("server: 區塊內找不到 port 行")
open(path, "w", encoding="utf-8").write("".join(lines))
PY
  [ $? -eq 0 ] || die "埠位修改失敗（設定檔已備份：$CONFIG_BAK）"
  NEW_PORT="$(awk '
    /^server:[[:space:]]*$/ { s=1; next }
    s && /^[^[:space:]#]/       { s=0 }
    s && $1 == "port:"          { gsub(/[^0-9]/,"",$2); print $2; exit }
  ' "$CONFIG")"
  [ "$NEW_PORT" = "$WANT_PORT" ] || die "埠位修改後讀回是 $NEW_PORT，預期 $WANT_PORT"
  ok "server.port: $OLD_PORT → $NEW_PORT"
fi

# ───────────────────────────────────────────── 4/6 安裝二進位
step "4/6 安裝二進位（原子替換）"
install -m 755 -o root -g root "$BIN" "${TARGET}.new.$$" || die "install 失敗，目標未動"
chmod u+x,g+x,o+x "${TARGET}.new.$$" || { rm -f "${TARGET}.new.$$"; die "無法設定執行位元"; }
[ -r "${TARGET}.new.$$" ] && [ -x "${TARGET}.new.$$" ] || { rm -f "${TARGET}.new.$$"; die "暫存檔不可讀/不可執行"; }
mv -f "${TARGET}.new.$$" "$TARGET" || { rm -f "${TARGET}.new.$$"; die "原子替換失敗"; }
LANDED="$(sha256sum "$TARGET" | awk '{print $1}')"
[ "$LANDED" = "$EXPECT" ] || die "落地後雜湊與 sidecar 不符（$LANDED != $EXPECT）"
ok "已替換，落地 sha256 = $LANDED"

step "4b/6 同步 Web 資產"
for rel in \
  web/templates/index.html \
  web/static/js/i18n.js \
  web/static/js/vulnerability.js \
  web/static/js/security-ops.js \
  web/static/js/router.js \
  web/static/js/auth.js \
  web/static/js/projects.js \
  web/static/js/recon.js \
  web/static/js/redirect-verify.js \
  web/static/js/loan-cases.js \
  web/static/js/hitl.js \
  web/static/js/monitor.js \
  web/static/js/chat.js \
  web/static/js/scope-extension.js \
  web/static/css/xss.css \
  web/static/css/style.css \
  web/static/css/security-ops.css \
  web/static/css/redirect-verify.css \
  web/static/css/tech-grid.css \
  web/static/i18n/zh-CN.json \
  web/static/i18n/en-US.json
do
  [ -f "$SRC_ROOT/$rel" ] || { bad "工作區缺少 $rel，略過"; continue; }
  install -D -m 644 "$SRC_ROOT/$rel" "$CURRENT/$rel" || bad "同步 $rel 失敗"
done
ok "Web 資產同步完成"

# ───────────────────────────────────────────── 5/6 重啟
step "5/6 確保 PostgreSQL / Control Plane 並重啟 $SERVICE"
if ! systemctl is-active --quiet postgresql@18-main.service; then
  systemctl start postgresql@18-main.service && ok "已啟動 postgresql@18-main.service" || bad "啟動 postgresql@18-main.service 失敗"
fi
if ! systemctl is-active --quiet jysec-control-plane.service; then
  systemctl restart jysec-control-plane.service && ok "已重啟 jysec-control-plane.service" || bad "重啟 jysec-control-plane.service 失敗"
fi
systemctl restart "$SERVICE" || die "重啟失敗（回滾指令：cp -p '$BIN_BAK' '$TARGET' && systemctl restart $SERVICE）"

step "6/6 等待健康並驗證"
for i in $(seq 1 60); do
  if curl -fsS --max-time 5 "http://127.0.0.1:${WANT_PORT}/" >/dev/null 2>&1; then
    ok "Web 埠 ${WANT_PORT} 已回應（等待 ${i}0 秒內）"
    break
  fi
  [ "$i" -lt 60 ] || { bad "Web 埠 ${WANT_PORT} 仍未回應"; }
  sleep 10
done
systemctl is-active "$SERVICE" && ok "$SERVICE active" || bad "$SERVICE 不是 active"

# 標頭必須用 bash 陣列傳，不能把 "Name: value" 塞進 $(...) 再讓 word splitting
# 拆開——那會把 "X-MCP-Token: <value>" 變成兩個 argv，curl 收到空值標頭 → 401。
MCP_AUTH_HEADER="$(awk '
  /^mcp:[[:space:]]*$/            { s=1; next }
  s && /^[^[:space:]#]/           { s=0 }
  s && $1 == "auth_header:"       { gsub(/["\x27]/,"",$2); print $2; exit }
' "$CONFIG")"
MCP_AUTH_VALUE="$(awk '
  /^mcp:[[:space:]]*$/            { s=1; next }
  s && /^[^[:space:]#]/           { s=0 }
  s && $1 == "auth_header_value:" { gsub(/["\x27]/,"",$2); print $2; exit }
' "$CONFIG")"
MCP_AUTH_ARGS=()
if [ -n "$MCP_AUTH_HEADER" ] && [ -n "$MCP_AUTH_VALUE" ]; then
  MCP_AUTH_ARGS=(-H "${MCP_AUTH_HEADER}: ${MCP_AUTH_VALUE}")
fi
TOOLS="$(curl -fsS --max-time 15 -X POST "http://127.0.0.1:${MCP_PORT}/mcp" \
  -H 'Content-Type: application/json' \
  "${MCP_AUTH_ARGS[@]+"${MCP_AUTH_ARGS[@]}"}" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' 2>/dev/null \
  | python3 -c 'import json,sys;print(len(json.load(sys.stdin)["result"]["tools"]))' 2>/dev/null)"
if [ -n "${TOOLS:-}" ]; then ok "平台 MCP (${MCP_PORT}) 工具數 = $TOOLS"; else bad "平台 MCP 工具清單取不到（401 表示沒帶對 X-MCP-Token，請檢查 mcp.auth_header_value）"; fi

# 公開入口（gateway/edge 的上游就是 8080；上游接回來後才會脫離 503 service_restarting）
EDGE_CODE="$(curl -sk --max-time 10 -o /tmp/jysec_edge_check.txt -w '%{http_code}' \
  -H 'Host: jysecai.utown.cc.cd' https://127.0.0.1/ 2>/dev/null || echo 000)"
if [ "$EDGE_CODE" = "200" ]; then
  ok "公開入口已恢復（https://127.0.0.1/ → 200）"
else
  bad "公開入口仍是 HTTP $EDGE_CODE：$(head -c 120 /tmp/jysec_edge_check.txt 2>/dev/null)"
  bad "（若仍 503 service_restarting，請確認 gateway 的上游埠與 jysec-core 相同）"
fi

# watchdog 的健康探測條件（它就是靠這條判定要不要重啟核心）
if curl -fsS --max-time 8 "http://127.0.0.1:${WANT_PORT}/" >/dev/null 2>&1; then
  ok "watchdog 探測路徑 http://127.0.0.1:${WANT_PORT}/ 已回應（watchdog 不再會誤重啟）"
else
  bad "watchdog 探測路徑仍無回應"
fi

cat > "${TARGET}.deploy-receipt.json" <<EOF
{
  "deployed_at": "$(date -Is)",
  "sha256": "$LANDED",
  "source_path": "$BIN",
  "target_path": "$TARGET",
  "backup_binary": "$BIN_BAK",
  "backup_config": "$CONFIG_BAK",
  "server_port": "$WANT_PORT",
  "mcp_tools": "${TOOLS:-unknown}"
}
EOF
ok "部署收據 → ${TARGET}.deploy-receipt.json"

printf '\n[部署完成] sha256=%s  server.port=%s\n' "$LANDED" "$WANT_PORT"
printf '  回滾指令：cp -p %s %s && cp -p %s %s && systemctl restart %s\n' \
  "$BIN_BAK" "$TARGET" "$CONFIG_BAK" "$CONFIG" "$SERVICE"
