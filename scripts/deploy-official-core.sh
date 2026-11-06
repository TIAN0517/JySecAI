#!/bin/bash
# 把這份工作區的程式換上正式 jysec-core，資料庫仍用 /var/lib/jysecai/core/config.yaml。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
CURRENT=/opt/jysecai/core/current
RELEASES=/opt/jysecai/core/releases
install -d "$RELEASES"
cp -a "$CURRENT/jysec-core" "$RELEASES/jysec-core.${STAMP}.bak"
install -m 755 "$ROOT/jysec-core-linux" "$CURRENT/jysec-core"
chown root:root "$CURRENT/jysec-core"
for rel in \
  web/templates/index.html \
  web/static/js/vulnerability.js \
  web/static/js/security-ops.js \
  web/static/js/router.js \
  web/static/js/auth.js \
  web/static/js/projects.js \
  web/static/js/recon.js \
  web/static/js/redirect-verify.js \
  web/static/js/loan-cases.js \
  web/static/css/xss.css \
  web/static/css/security-ops.css \
  web/static/css/redirect-verify.css \
  web/static/css/tech-grid.css \
  web/static/i18n/zh-CN.json \
  web/static/i18n/en-US.json
do
  install -D -m 644 "$ROOT/$rel" "$CURRENT/$rel"
done
systemctl restart jysec-core
sleep 8
systemctl is-active jysec-core

# 健康檢查埠位必須跟正式 config 的 server.port 一致。
# 寫死 8080 會誤判：正式核心目前跑在 9898，寫死 8080 會讓部署後的驗證直接失敗。
# fallback 也跟著更新——埠位已經搬過兩次（8080 → 18082 → 9898），
# fallback 停在舊值只會讓「讀不到 port」時的退路連到一個沒人監聽的埠。
CORE_PORT="$(awk '
  /^server:[[:space:]]*$/            { s=1; next }
  s && /^[^[:space:]#]/              { s=0 }
  s && $1=="port:"                   { gsub(/[^0-9]/,"",$2); print $2; exit }
' /var/lib/jysecai/core/config.yaml)"
[ -n "$CORE_PORT" ] || CORE_PORT=9898
curl -fsS "http://127.0.0.1:${CORE_PORT}/" | grep -o 'vulnerability.js?v=[^"]*'
