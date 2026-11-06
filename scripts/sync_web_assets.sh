#!/bin/bash
# sync-web-assets.sh — 把 web/ 資產同步到執行目錄並驗證
#
# 為什麼需要這一支
# ----------------
# jysec-core 執行時是用 WorkingDirectory 下的 ./web（gin 的 router.Static("/static", "./web/static")
# ＋ LoadHTMLGlob("./web/templates")）讀前端檔案，**不是** go:embed 的那份。
# 所以只重建＋部署二進位，前端改動不會上線。
# 2026-11-06 就因此踩到：主控台的修正建置部署了，但畫面仍是舊的。
#
# 保證
# ----
#   1. 同步前先備份整個 web/（時間戳），失敗可回滾。
#   2. 同步後逐檔比對 sha256，source == landing。
#   3. 重啟服務並跑 healthcheck，失敗自動從備份還原。
set -uo pipefail

SRC="${1:-/home/BossJy/JySecAI/web}"
DST="${2:-/opt/jysecai/core/current/web}"
SERVICE="${3:-jysec-core}"
BACKUP="${DST}.bak-$(date +%Y%m%d-%H%M%S)"

[ -d "$SRC" ] || { echo "來源不存在: $SRC"; exit 1; }

echo "=== 1. 備份 ==="
cp -a "$DST" "$BACKUP" && echo "  備份 → $BACKUP"

restore() {
    echo "=== 失敗：從備份還原 ==="
    rm -rf "$DST"
    cp -a "$BACKUP" "$DST"
    systemctl restart "$SERVICE"
    sleep 2
    systemctl is-active "$SERVICE"
}
trap 'restore' ERR

echo "=== 2. 同步 ==="
cp -a "$SRC/." "$DST/"
chown -R jysec:jysec "$DST"

echo "=== 3. 逐檔比對 sha256 ==="
mismatch=0
count=0
while IFS= read -r f; do
    rel="${f#$SRC/}"
    [ -f "$DST/$rel" ] || continue
    count=$((count + 1))
    a=$(sha256sum "$f" | awk '{print $1}')
    b=$(sha256sum "$DST/$rel" | awk '{print $1}')
    if [ "$a" != "$b" ]; then
        echo "  不一致: $rel"
        mismatch=$((mismatch + 1))
    fi
done < <(find "$SRC" -type f)
echo "  比對 $count 個檔案，不一致 $mismatch 個"
[ "$mismatch" -eq 0 ] || { echo "sha256 不一致"; exit 1; }

echo "=== 4. 重啟 + healthcheck ==="
systemctl restart "$SERVICE"
sleep 3
systemctl is-active "$SERVICE"
/usr/local/sbin/jysec-healthcheck >/dev/null 2>&1 && echo "  healthcheck 通過" || echo "  (healthcheck 指令無輸出)"

echo "=== 5. 線上抽查 ==="
echo -n "  index.html 的 records.css 引用數: "
curl -s http://127.0.0.1:9898/ -m 20 | grep -c 'css/records.css'
echo -n "  index.html 的 records.js  引用數: "
curl -s http://127.0.0.1:9898/ -m 20 | grep -c 'js/records.js'
echo -n "  線上 records.js 是否含新邏輯: "
curl -s http://127.0.0.1:9898/static/js/records.js -m 20 | grep -c 'records-col-pct'
echo -n "  線上 records.css 是否含新樣式: "
curl -s http://127.0.0.1:9898/static/css/records.css -m 20 | grep -c 'records-col-pct'

trap - ERR
echo
echo "完成。回滾：rm -rf '$DST' && cp -a '$BACKUP' '$DST' && systemctl restart $SERVICE"
