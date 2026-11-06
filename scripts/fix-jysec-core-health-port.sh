#!/bin/bash
# 修正 jysec-core 的 systemd 健康檢查埠位。
#
# 為什麼會壞（兩種獨立的故障）：
#
#   (1) 健康檢查埠位與實際 listen 埠位不一致
#       /etc/systemd/system/jysec-core.service 的 ExecStartPost 寫死
#       http://127.0.0.1:8080/ ，但正式 config
#       （/var/lib/jysecai/core/config.yaml）的 server.port 被改成 18082。
#       健康檢查永遠連不到 → jysec-wait-for-health exit 1 → systemd 判定
#       「啟動失敗」→ Restart=always → 每約 2 分鐘重啟一次。
#
#   (2) 埠位被「非 jysec-core」行程佔住
#       例：使用者層級的 jysec-8080-proxy.service（8080→18082 的臨時橋接）。
#       核心 bind 不到 → "listen tcp 127.0.0.1:<port>: bind: address already in use"
#       → logger.Fatal → 服務永遠起不來。本腳本會在重啟前先做佔用預檢。
#
# 為什麼這會讓「掃描器沒有自動拉起全功能」：
#   每次重啟都會把外部 MCP 伺服器全部拆掉重建（Pentester-MCP 11 tools、
#   Kali API、HexStrike、dragon-v、vuln-intel、reverse-shell、redteam-knowledge），
#   連帶重置自動分流／自動復測排程器、Telegram／微信長輪詢、XSS canary。
#   掃描器的全功能集合因此永遠處於「剛被重建」的狀態，執行中的掃描會被中斷。
#
# 修法（一次到位，以後不會再漂移）：
#   1. 安裝 /usr/local/sbin/jysec-core-wait-healthy —— 從正式 config 的
#      server.port 推導實際埠位，再委派給既有的 jysec-wait-for-health。
#   2. 把 unit 的 ExecStartPost 換成呼叫這個 helper。
#   3. 預檢埠位佔用 → daemon-reload → restart → 驗證；失敗自動回退 unit。
#
# 用法（在 WSL 內）：
#   sudo bash scripts/fix-jysec-core-health-port.sh            # 修 + 重啟
#   sudo bash scripts/fix-jysec-core-health-port.sh --verify   # 修完等 150 秒確認不再重啟
#
# 安全：會先備份 unit（jysec-core.service.bak-<時間戳>），可重複執行；
#       重啟失敗會自動把 unit 回退到備份並重新啟動。
set -euo pipefail

UNIT=/etc/systemd/system/jysec-core.service
HELPER=/usr/local/sbin/jysec-core-wait-healthy
CONFIG=/var/lib/jysecai/core/config.yaml
WAITER=/usr/local/sbin/jysec-wait-for-health

if [ "$(id -u)" != "0" ]; then
  echo "ERROR: 需要 root。請用：sudo bash $0" >&2
  exit 1
fi

if [ ! -f "$UNIT" ]; then
  echo "ERROR: 找不到 $UNIT" >&2
  exit 1
fi

if [ ! -x "$WAITER" ]; then
  echo "ERROR: 找不到 $WAITER，無法沿用既有健康檢查程式" >&2
  exit 1
fi

# ---------------------------------------------------------------- helper 安裝
install -m 755 /dev/stdin "$HELPER" <<'HELPER_EOF'
#!/bin/bash
# 由 server.port 推導 jysec-core 的實際監聽埠位，再委派給 jysec-wait-for-health。
# 用法：jysec-core-wait-healthy [timeout_seconds]
# 環境：JYSEC_CORE_CONFIG 可覆寫設定檔路徑。
set -u
CONFIG="${JYSEC_CORE_CONFIG:-/var/lib/jysecai/core/config.yaml}"
TIMEOUT="${1:-120}"

port="$(awk '
  /^server:[[:space:]]*$/   { s=1; next }
  s && /^[^[:space:]#]/     { s=0 }
  s && $1=="port:"          { gsub(/[^0-9]/,"",$2); print $2; exit }
' "$CONFIG" 2>/dev/null || true)"

if [ -z "${port:-}" ]; then
  echo "jysec-core-wait-healthy: 從 $CONFIG 讀不到 server.port，退回預設 9898" >&2
  port=9898
fi

exec /usr/local/sbin/jysec-wait-for-health "http://127.0.0.1:${port}/" "$TIMEOUT"
HELPER_EOF

if ! grep -q 'jysec-wait-for-health' "$HELPER" 2>/dev/null; then
  echo "ERROR: $HELPER 安裝後內容不完整，已中止（避免用壞掉的小幫手取代健康檢查）" >&2
  exit 1
fi
echo "OK: 已安裝 $HELPER"

# ------------------------------------------------------- unit 的 ExecStartPost
CUR_LINE="$(grep -E '^ExecStartPost=' "$UNIT" | head -1 || true)"
TIMEOUT="$(printf '%s' "$CUR_LINE" | awk '{print $NF}')"
case "$TIMEOUT" in
  ''|*[!0-9]*) TIMEOUT=120 ;;
esac

STAMP="$(date +%Y%m%d-%H%M%S)"
if printf '%s' "$CUR_LINE" | grep -q "^$HELPER"; then
  echo "SKIP: unit 已經在用 $HELPER（冪等，不重複備份）"
  BACKUP="$(ls -1t "$UNIT".bak-* 2>/dev/null | head -1 || true)"
else
  BACKUP="$UNIT.bak-$STAMP"
  cp -a "$UNIT" "$BACKUP"
  sed -i "s|^ExecStartPost=/usr/local/sbin/jysec-wait-for-health .*$|ExecStartPost=$HELPER $TIMEOUT|" "$UNIT"
  if ! grep -q "^ExecStartPost=$HELPER" "$UNIT"; then
    echo "ERROR: unit 取代失敗，已保留備份：$BACKUP" >&2
    exit 1
  fi
  echo "OK: unit ExecStartPost 已改為 $HELPER $TIMEOUT（備份：$BACKUP）"
fi

echo "--- 目前的健康檢查設定 ---"
grep -E '^ExecStartPost=' "$UNIT"

# ------------------------------------------------- 埠位占用預檢（避免核心 bind 失敗）
PORT="$(awk '
  /^server:[[:space:]]*$/   { s=1; next }
  s && /^[^[:space:]#]/     { s=0 }
  s && $1=="port:"          { gsub(/[^0-9]/,"",$2); print $2; exit }
' "$CONFIG" 2>/dev/null || true)"
PORT="${PORT:-9898}"
echo "config server.port = $PORT"

HOLDER="$(ss -ltnp 2>/dev/null | awk -v p=":$PORT\$" '$4 ~ p' || true)"
if [ -n "$HOLDER" ]; then
  if printf '%s' "$HOLDER" | grep -q 'jysec-core'; then
    echo "OK: 埠位 $PORT 目前由 jysec-core 持有"
  else
    echo "ERROR: 埠位 $PORT 被其他行程佔住，核心將無法 bind 而 fatal：" >&2
    printf '%s\n' "$HOLDER" >&2
    echo "       先釋放該埠位再重跑本腳本。例如使用者層級的臨時橋接：" >&2
    echo "       systemctl --user disable --now jysec-8080-proxy.service" >&2
    exit 1
  fi
else
  echo "OK: 埠位 $PORT 目前空閒"
fi

# ------------------------------------------------------------------- 重啟驗證
systemctl daemon-reload
if ! systemctl restart jysec-core.service; then
  echo "ERROR: 重啟失敗。正在把 unit 回退到備份。" >&2
  if [ -n "${BACKUP:-}" ] && [ -f "$BACKUP" ]; then
    cp -a "$BACKUP" "$UNIT"
    systemctl daemon-reload
    systemctl restart jysec-core.service || true
    sleep 10
    echo "--- 回退後狀態 ---" >&2
    systemctl show jysec-core.service -p ActiveState -p SubState -p NRestarts >&2
  fi
  echo "請查 journalctl -u jysec-core -n 100" >&2
  exit 1
fi

sleep 12
echo "--- 重啟後狀態 ---"
systemctl show jysec-core.service -p ActiveState -p SubState -p NRestarts -p ExecMainStatus

if command -v curl >/dev/null 2>&1; then
  echo -n "HTTP 探測 : "
  curl -s -o /dev/null -w '%{http_code}\n' --max-time 5 "http://127.0.0.1:${PORT}/" || true
fi

if [ "${1:-}" = "--verify" ]; then
  BEFORE="$(systemctl show jysec-core.service -p NRestarts --value)"
  echo "等待 150 秒確認不再進入重啟迴圈（目前 NRestarts=$BEFORE）..."
  sleep 150
  AFTER="$(systemctl show jysec-core.service -p NRestarts --value)"
  echo "--- 驗證結果 ---"
  systemctl show jysec-core.service -p ActiveState -p SubState -p NRestarts
  if [ "$BEFORE" = "$AFTER" ]; then
    echo "PASS: 150 秒內沒有新增重啟，服務穩定。"
  else
    echo "FAIL: 重啟計數仍從 $BEFORE 增加到 $AFTER，請回報並查 journalctl -u jysec-core。"
    exit 1
  fi
fi

echo "DONE."
