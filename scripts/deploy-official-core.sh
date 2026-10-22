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
  web/static/css/xss.css \
  web/static/css/security-ops.css \
  web/static/i18n/zh-CN.json \
  web/static/i18n/en-US.json
do
  install -D -m 644 "$ROOT/$rel" "$CURRENT/$rel"
done
systemctl restart jysec-core
sleep 8
systemctl is-active jysec-core
curl -fsS http://127.0.0.1:8080/ | grep -o 'vulnerability.js?v=[^"]*'
