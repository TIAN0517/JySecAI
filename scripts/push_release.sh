#!/bin/bash
# push_release.sh — 建立正式 release 並原子切換 current（可回滾）
#
# 步驟
#   1. 由現況 release 複製出新 release（去掉舊的 *.bak 檔以省空間）
#   2. 裝入新二進位與 web 資產（並逐檔校驗 sha256）
#   3. 原子切換 symlink current → 新 release
#   4. 重啟 + healthcheck；失敗自動切回舊 release
#   5. 列印回滾指令
set -uo pipefail

ROOT=/home/BossJy/JySecAI
BASE=/opt/jysecai/core
STAMP=$(date +%Y%m%d-%H%M%S)
OLD=$(readlink -f "$BASE/current")
NEW="$BASE/releases/${STAMP}-records-console-v2"
SERVICE=jysec-core

echo "=== 1. 建立新 release ==="
echo "  舊：$OLD"
echo "  新：$NEW"
mkdir -p "$NEW"
# 複製現況（排除舊備份）
tar -C "$OLD" --exclude='jysec-core.bak-*' --exclude='*.bak-*' -cf - . 2>/dev/null | tar -C "$NEW" -xf -
echo "  複製完成：$(du -sh "$NEW" | cut -f1)"

echo
echo "=== 2. 裝入新二進位 + web 資產 ==="
install -m 755 "$ROOT/build/releases/jysec-core" "$NEW/jysec-core"
chown root:root "$NEW/jysec-core"
cp -a "$ROOT/web/." "$NEW/web/"
mkdir -p "$NEW/build/releases"
for b in records-ingest scan-runner; do
    [ -f "$ROOT/build/releases/$b" ] && install -m 755 "$ROOT/build/releases/$b" "$NEW/build/releases/$b"
done
# 2026-11-06 硬化：release 目錄與二進位必須 root 持有。
# 服務以 jysec 執行 —— 若目錄與二進位屬 jysec，jysec 就能 unlink 並置換自己
# 執行的二進位。把檔案 chmod 600 也擋不住 unlink；能擋住的是「父目錄不可寫」。
# console 的技能／角色／子代理編輯功能會寫入 web/、skills/、roles/、agents/
# （internal/handler/skills.go、role.go、markdown_agents.go），這幾個子目錄
# 維持 jysec 可寫；其餘一律 root 持有。
chown -R root:root "$NEW"
chmod -R u=rwX,go=rX "$NEW"
for d in web skills roles agents; do
    if [ -d "$NEW/$d" ]; then
        chown -R jysec:jysec "$NEW/$d"
        chmod -R u+rwX,go+rX "$NEW/$d"
    fi
done
chown root:root "$NEW/jysec-core" 2>/dev/null
chmod 755 "$NEW/jysec-core" 2>/dev/null

SRC_SHA=$(sha256sum "$ROOT/build/releases/jysec-core" | awk '{print $1}')
NEW_SHA=$(sha256sum "$NEW/jysec-core" | awk '{print $1}')
if [ "$SRC_SHA" != "$NEW_SHA" ]; then echo "  二進位 sha256 不一致"; exit 1; fi
echo "  二進位 sha256 一致：${SRC_SHA:0:16}…"
MIS=0; CNT=0
while IFS= read -r f; do
  rel="${f#$ROOT/web/}"
  [ -f "$NEW/web/$rel" ] || continue
  CNT=$((CNT+1))
  a=$(sha256sum "$f" | awk '{print $1}'); b=$(sha256sum "$NEW/web/$rel" | awk '{print $1}')
  [ "$a" = "$b" ] || { MIS=$((MIS+1)); echo "  不一致：$rel"; }
done < <(find "$ROOT/web" -type f)
echo "  web 資產：$CNT 個檔案，不一致 $MIS"
[ "$MIS" -eq 0 ] || exit 1

echo
echo "=== 3. 原子切換 current ==="
ln -sfn "$NEW" "$BASE/current.new"
mv -T "$BASE/current.new" "$BASE/current"
echo "  current → $(readlink -f "$BASE/current")"

echo
echo "=== 4. 重啟 + healthcheck ==="
systemctl restart "$SERVICE"
# 核心冷啟動可能需數分鐘（7.1GB 生產庫 + WAL/migration）。原本 sleep 6 就用
# systemctl is-active 判定，而服務此時通常仍在 activating（ExecStartPost 會等
# 健康檢查），is-active 對 activating 回傳非零 → 誤判失敗而無謂回滾。
# 另外 jysec-healthcheck 在核心掛掉時會「自行重啟服務並回傳 0」，不適合當部署閘門。
# 改用 jysec-core-wait-healthy 等待實際可用，再確認服務狀態。
if /usr/local/sbin/jysec-core-wait-healthy 300 >/dev/null 2>&1 && systemctl is-active --quiet "$SERVICE"; then
  echo "  服務正常，healthcheck 通過"
else
  echo "  ✗ 失敗 → 自動回滾到 $OLD"
  ln -sfn "$OLD" "$BASE/current.new"; mv -T "$BASE/current.new" "$BASE/current"
  systemctl restart "$SERVICE"; sleep 5
  systemctl is-active "$SERVICE"
  exit 1
fi

echo
echo "=== 5. 部署收據 ==="
cat > "$NEW/DEPLOY-RECEIPT.txt" <<EOF
release      : $(basename "$NEW")
previous     : $(basename "$OLD")
binary_sha256: $NEW_SHA
web_files    : $CNT (全部一致)
pushed_at    : $(date -Iseconds)
rollback     : ln -sfn $OLD $BASE/current && systemctl restart $SERVICE
EOF
cat "$NEW/DEPLOY-RECEIPT.txt"

echo
echo "完成。回滾指令："
echo "  ln -sfn $OLD $BASE/current && systemctl restart $SERVICE"
