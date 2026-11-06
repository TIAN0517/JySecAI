#!/usr/bin/env bash
# 一鍵把「3D 立體格子背景 + 貸款案件頁 + /api/loan/* + 貸款資料庫 + OAuth Critical 漏洞」
# 一次送上正式 jysec-core，並在上線後自我驗證。
#
# 為什麼需要這一支
#   2026-10-28 發現兩個會讓「部署成功但功能沒上線」的坑：
#     1. 舊的 deploy-official-core.sh 搬的是 $ROOT/jysec-core-linux，
#        那是 2026-10-25 的舊 binary，裡面沒有任何 /loan/* 路由 ——
#        部署腳本會回報成功，貸款頁卻是 404。
#     2. 舊腳本沒有安裝 data/loan_cases.db，也沒有落 OAuth 漏洞，
#        所以「資料有、但網站上看不到」。
#   這支把 binary（含 sidecar 雜湊守門）、靜態資源、資料庫、漏洞落庫
#   綁成一次可驗證的部署；任一步失敗自動回滾 binary 並重啟。
#
# 用法（需要 sudo）
#   sudo bash scripts/deploy-loan-grid-vuln.sh
#
# 前置（不需要 root，腳本會檢查）
#   bash scripts/build-jysec-core.sh                 # 建置 binary + sidecar
#   python3 scripts/import_loan_cases.py             # 匯入貸款資料庫

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CURRENT=/opt/jysecai/core/current
RELEASES=/opt/jysecai/core/releases
CONFIG=/var/lib/jysecai/core/config.yaml
STAMP="$(date +%Y%m%d-%H%M%S)"

BIN="$ROOT/build/releases/jysec-core"
SIDECAR="$BIN.sha256"
LOAN_DB="$ROOT/data/loan_cases.db"
EVIDENCE_DIR="${EVIDENCE_DIR:-/mnt/c/Users/Administrator/Desktop/chailease_membercenter_oauth_crypto_evidence}"
PUBLIC_HOST="jysecai.utown.cc.cd"

die()  { printf '\n[abort] %s\n' "$*" >&2; exit 2; }
step() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
ok()   { printf '  [OK] %s\n' "$*"; }
bad()  { printf '  [!!] %s\n' "$*"; }

[ "$(id -u)" -eq 0 ] || die "請用 sudo 執行"
[ -f "$BIN" ]      || die "找不到 $BIN，請先執行 scripts/build-jysec-core.sh"
[ -f "$SIDECAR" ]  || die "找不到 $SIDECAR（建置腳本會一併產生）"
[ -f "$LOAN_DB" ]  || die "找不到 $LOAN_DB，請先執行 scripts/import_loan_cases.py"

step "0. 部署前守門：source == sidecar"
SRC_SHA="$(awk 'NF{print $1; exit}' "$SIDECAR")"
REAL_SHA="$(sha256sum "$BIN" | awk '{print $1}')"
[ "$SRC_SHA" = "$REAL_SHA" ] || die "binary 雜湊與 sidecar 不一致：$REAL_SHA != $SRC_SHA
（有人動過 build 產物。請重新 build，勿手改。）"
ok "binary sha256 = $REAL_SHA"
# 2026-10-28 修正：原本寫成 `strings "$BIN" | grep -q -- "$sym"`。
# 在 pipefail 下這會誤判 —— grep -q 一找到就 exit，strings 收到 SIGPIPE 回 141，
# 管線整條被判失敗，於是明明 binary 內有 /loan/* 路由卻報「找不到路由」並中止部署。
# 改成：先把 strings 輸出寫進暫存檔，再逐條 grep -F。
ROUTE_DUMP="$(mktemp)"
trap 'rm -f "$ROUTE_DUMP"' EXIT
strings "$BIN" > "$ROUTE_DUMP"
for sym in "/loan/summary" "/loan/cases" "/loan/case" "/loan/applications" "/loan/tables" "/loan/verify" "/loan/export" "/loan/classification"; do
  grep -qF -- "$sym" "$ROUTE_DUMP" || die "binary 內找不到路由 $sym —— 這不是含貸款功能的版本，拒絕部署"
done
ok "binary 內含 8 條 /loan/* 路由（含 /loan/classification 分類字典）"

install -d "$RELEASES"
BACKUP="$RELEASES/jysec-core.${STAMP}.bak"
[ -f "$CURRENT/jysec-core" ] && cp -a "$CURRENT/jysec-core" "$BACKUP" && ok "已備份舊 binary → $BACKUP"

rollback() {
  bad "部署失敗，開始回滾"
  if [ -f "$BACKUP" ]; then
    cp -a "$BACKUP" "$CURRENT/jysec-core"
    systemctl restart jysec-core >/dev/null 2>&1 || true
    ok "已還原舊 binary 並重啟服務"
  fi
  systemctl is-active jysec-core || true
}

step "1. 安裝 binary（先 .tmp 再原子替換）"
install -m 755 "$BIN" "$CURRENT/jysec-core.tmp"
mv -f "$CURRENT/jysec-core.tmp" "$CURRENT/jysec-core"
chown root:root "$CURRENT/jysec-core"
LAND_SHA="$(sha256sum "$CURRENT/jysec-core" | awk '{print $1}')"
[ "$LAND_SHA" = "$SRC_SHA" ] || { bad "落地後雜湊不符：$LAND_SHA != $SRC_SHA"; rollback; exit 2; }
ok "落地 binary sha256 = $LAND_SHA（與驗證用同一份）"

step "2. 安裝靜態資源"
for rel in \
  web/templates/index.html \
  web/static/css/tech-grid.css \
  web/static/js/loan-cases.js \
  web/static/js/router.js
do
  [ -f "$ROOT/$rel" ] || { bad "來源缺少 $rel"; rollback; exit 2; }
  install -D -m 644 "$ROOT/$rel" "$CURRENT/$rel"
  ok "$rel  ($(wc -c < "$ROOT/$rel") bytes)"
done

step "3. 安裝貸款資料庫（handler 預設讀相對路徑 data/loan_cases.db）"
install -d -m 755 "$CURRENT/data"
install -m 644 "$LOAN_DB" "$CURRENT/data/loan_cases.db"
chown jysec:jysec "$CURRENT/data/loan_cases.db"
ok "$CURRENT/data/loan_cases.db ($(wc -c < "$LOAN_DB") bytes)"

step "4. 找出正式 conversations.db 路徑"
[ -f "$CONFIG" ] || { bad "找不到 $CONFIG"; rollback; exit 2; }
DB_REL="$(awk '
  /^[^[:space:]#]/ { sec=$1; sub(/:$/,"",sec) }
  sec=="database" && $1=="path:" { gsub(/"/,"",$2); print $2; exit }
' "$CONFIG")"
DB_REL="${DB_REL:-data/conversations.db}"
case "$DB_REL" in
  /*) DB_PATH="$DB_REL" ;;
  *)  DB_PATH="$CURRENT/$DB_REL" ;;
esac
[ -f "$DB_PATH" ] || { bad "找不到正式資料庫：$DB_PATH"; rollback; exit 2; }
ok "正式資料庫：$DB_PATH"

step "5. 重啟服務"
systemctl restart jysec-core
for i in $(seq 1 30); do
  if systemctl is-active --quiet jysec-core; then break; fi
  sleep 1
done
systemctl is-active --quiet jysec-core || { bad "服務重啟後未 active"; rollback; exit 2; }
ok "jysec-core active"

step "6. 落 OAuth Critical 漏洞 + 證據"
systemctl stop jysec-core
install -d -m 755 /var/lib/jysecai/core/evidence
EV_DST=/var/lib/jysecai/core/evidence/oauth_crypto
python3 "$ROOT/scripts/seed_oauth_vuln.py" --db "$DB_PATH" \
        --evidence-dir "$EVIDENCE_DIR" --copy-evidence-to "$EV_DST"
SEED_RC=$?
systemctl start jysec-core
[ "$SEED_RC" -eq 0 ] || { bad "漏洞落庫失敗"; rollback; exit 2; }
VROW="$(sqlite3 "$DB_PATH" "select id||' | '||severity||' | conf='||confidence from vulnerabilities where id='4c74bfbf-e298-4471-bb13-f8fa64ca187c';")"
[ -n "$VROW" ] || { bad "落庫後查不到該漏洞"; rollback; exit 2; }
ok "vulnerabilities 現有該筆：$VROW"

step "7. 上線後驗證"
CORE_PORT="$(awk '
  /^server:[[:space:]]*$/ { s=1; next }
  s && /^[^[:space:]#]/ { s=0 }
  s && $1=="port:" { gsub(/[^0-9]/,"",$2); print $2; exit }
' "$CONFIG")"
[ -n "$CORE_PORT" ] || CORE_PORT=18443
ok "正式核心 port = $CORE_PORT"

probe() { curl -sk -o /dev/null -w "%{http_code}" --max-time 10 \
          --resolve "$PUBLIC_HOST:$CORE_PORT:127.0.0.1" "$1"; }

LOAN_CODE="$(probe "https://$PUBLIC_HOST:$CORE_PORT/api/loan/summary")"
if [ "$LOAN_CODE" = "404" ]; then
  bad "/api/loan/summary 回 404 —— 路由沒進來"
  rollback; exit 2
fi
ok "/api/loan/summary → HTTP $LOAN_CODE（401 = 路由已註冊、需登入，符合預期）"

CSS_CODE="$(probe "https://$PUBLIC_HOST:$CORE_PORT/static/css/tech-grid.css")"
[ "$CSS_CODE" = "200" ] || { bad "tech-grid.css → $CSS_CODE"; rollback; exit 2; }
ok "/static/css/tech-grid.css → 200"

JS_CODE="$(probe "https://$PUBLIC_HOST:$CORE_PORT/static/js/loan-cases.js")"
[ "$JS_CODE" = "200" ] || { bad "loan-cases.js → $JS_CODE"; rollback; exit 2; }
ok "/static/js/loan-cases.js → 200"

HTML_CODE="$(probe "https://$PUBLIC_HOST:$CORE_PORT/")"
[ "$HTML_CODE" = "200" ] || { bad "首頁 → $HTML_CODE"; rollback; exit 2; }
ok "首頁 → 200"

step "完成"
printf '  部署收據\n'
printf '    binary  : %s\n' "$LAND_SHA"
printf '    備份    : %s\n' "$BACKUP"
printf '    資料庫  : %s\n' "$DB_PATH"
printf '    證據落地: %s\n' "$EV_DST"
printf '    port    : %s\n' "$CORE_PORT"
printf '\n  對外驗證（需平台帳號登入）：\n'
printf '    https://%s/  → 側欄「貸款案件」\n' "$PUBLIC_HOST"
printf '\n  驗證後請執行：\n'
printf '    sqlite3 "%s" "select count(*) from vulnerabilities;"\n' "$DB_PATH"
printf '\n'
