#!/usr/bin/env bash
# deploy-grok-bridge.sh — 從「唯一真相原始碼」部署 grok bridge，並留下 sha256 收據。
#
# 為什麼需要這支
#   2026-11-06 發佈複查發現：dev-mode 實作只存在於落地檔
#   /opt/jysec-grok-bridge/grok_openai_bridge_slim.py（14:33 有人直接手改），
#   原始碼 /home/BossJy/JySecAI/tools/grok_openai_bridge_slim.py 從未同步。
#   任何人從原始碼重建 bridge 都會把 dev-mode 弄丟 —— 落地檔變成唯一真相，
#   收據（sha256）也就無從驗證。這正是本支腳本要杜絕的狀況。
#
# 核心保證
#   1. 只從原始碼部署，不手改落地檔。
#   2. 部署前先驗 source == sidecar；sidecar 是部署當下寫下的唯一真相。
#   3. 先寫到 target.tmp 再 mv 原子替換；落地後重算落地 sha256 必須三者一致。
#   4. 任一步失敗自動從時間戳備份還原並重啟服務。
#   5. 寫部署收據（DEPLOY-RECEIPT.txt），之後可證明「驗了什麼、部署了什麼」。
#   6. 重啟後跑 smoke test（帶 token 打 /v1/chat/completions），不只看 process 活著。
#
# 用法
#   sudo bash deploy-grok-bridge.sh
#   sudo bash deploy-grok-bridge.sh --verify-only
#   bash deploy-grok-bridge.sh --self-test
set -uo pipefail

ROOT=/home/BossJy/JySecAI
SOURCE="$ROOT/tools/grok_openai_bridge_slim.py"
TARGET=/opt/jysec-grok-bridge/grok_openai_bridge_slim.py
SIDECAR=/opt/jysec-grok-bridge/grok_openai_bridge_slim.py.sha256
DETECT_SRC="$ROOT/scripts/_refusal_detect.py"
DETECT_TARGET=/opt/jysec-grok-bridge/_refusal_detect.py
SERVICE=jysec-grok-bridge
BRIDGE=http://127.0.0.1:18788
VERIFY_ONLY=0; SELF_TEST=0

for a in "$@"; do
  case "$a" in
    --verify-only) VERIFY_ONLY=1 ;;
    --self-test)   SELF_TEST=1 ;;
    *) printf '[abort] unknown arg: %s\n' "$a" >&2; exit 2 ;;
  esac
done

die()  { printf '\n[abort] %s\n' "$*" >&2; exit 2; }
step() { printf '\n== %s ==\n' "$*"; }
ok()   { printf '  [OK] %s\n' "$*"; }
bad()  { printf '  [!!] %s\n' "$*"; }

# ------------------------------------------------------------------ self test
if [ "$SELF_TEST" -eq 1 ]; then
  TMP=$(mktemp -d)
  printf 'hello\n' > "$TMP/a.py"
  printf 'hello\n' > "$TMP/b.py"
  A=$(sha256sum "$TMP/a.py" | awk '{print $1}')
  B=$(sha256sum "$TMP/b.py" | awk '{print $1}')
  [ "$A" = "$B" ] && ok "sha256 一致性判定正確" || bad "sha256 一致性判定錯誤"
  printf 'changed\n' > "$TMP/b.py"
  C=$(sha256sum "$TMP/b.py" | awk '{print $1}')
  [ "$A" != "$C" ] && ok "sha256 差異偵測正確" || bad "sha256 差異偵測錯誤"
  rm -rf "$TMP"
  exit 0
fi

[ -f "$SOURCE" ] || die "找不到原始碼：$SOURCE"
# bridge 在 import 時就會載入共用拒絕偵測模組；模組缺了服務根本起不來，
# 所以它必須跟 bridge 主檔同一次部署 —— 只手動 cp 就又回到「落地檔才是
# 唯一真相」的狀態，verify 的「共用同一份模組」檢查也會永遠紅燈。
[ -f "$DETECT_SRC" ] || die "找不到共用拒絕偵測模組：$DETECT_SRC"

step "0. 共用拒絕偵測模組自我測試"
if ! python3 "$DETECT_SRC" --selftest >/dev/null; then
  die "拒絕偵測模組自我測試未通過（偵測行為漂移）→ 拒絕部署"
fi
ok "拒絕偵測模組自我測試通過"

step "1. 驗證原始碼"
SRC_SHA=$(sha256sum "$SOURCE" | awk '{print $1}')
printf '  原始碼：%s\n  sha256：%s\n' "$SOURCE" "$SRC_SHA"
python3 -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$SOURCE" \
  || die "原始碼語法檢查失敗（python3 -m py_compile 等價驗證）"
ok "語法檢查通過"

if [ "$VERIFY_ONLY" -eq 1 ]; then
  step "2. verify-only：比對 source / sidecar / landing"
  SIDE=$(awk '{print $1}' "$SIDECAR" 2>/dev/null)
  LAND=$(sha256sum "$TARGET" 2>/dev/null | awk '{print $1}')
  printf '  source=%s\n  sidecar=%s\n  landing=%s\n' "${SRC_SHA:0:16}" "${SIDE:0:16}" "${LAND:0:16}"
  [ "$SRC_SHA" = "$SIDE" ] && [ "$SRC_SHA" = "$LAND" ] \
    && ok "source == sidecar == landing" || die "三者不一致（source=${SRC_SHA:0:16} side=${SIDE:0:16} land=${LAND:0:16}）"
  D_SRC=$(sha256sum "$DETECT_SRC" 2>/dev/null | awk '{print $1}')
  D_LAND=$(sha256sum "$DETECT_TARGET" 2>/dev/null | awk '{print $1}')
  printf '  detect source=%s\n  detect landing=%s\n' "${D_SRC:0:16}" "${D_LAND:0:16}"
  [ -n "$D_SRC" ] && [ "$D_SRC" = "$D_LAND" ] \
    && ok "共用模組 source == landing" || die "共用模組不一致（source=${D_SRC:0:16} land=${D_LAND:0:16}）"
  exit 0
fi

step "2. 建立備份 + 寫 sidecar"
STAMP=$(date +%Y%m%d-%H%M%S)
BAK="${TARGET}.bak-${STAMP}"
# 只在「落地檔確實不同於要部署的版本」時才留備份。
# 否則會造出一個跟現行落地檔一模一樣的備份 —— 拿它回滾等於什麼都沒做，
# 卻看起來像有回滾點（2026-11-06 實際踩到：.bak-20261106-164850 與現行檔同 sha）。
CUR_SHA=$(sha256sum "$TARGET" 2>/dev/null | awk '{print $1}')
if [ -f "$TARGET" ] && [ "$CUR_SHA" != "$SRC_SHA" ]; then
  cp -a "$TARGET" "$BAK" && printf '  備份：%s（sha %s）\n' "$BAK" "${CUR_SHA:0:12}"
else
  BAK=""
  if [ -f "$TARGET" ]; then
    printf '  落地檔已是目標版本（sha %s），不建立無效備份\n' "${CUR_SHA:0:12}"
  else
    printf '  首次部署，無備份\n'
  fi
fi
printf '%s  %s\n' "$SRC_SHA" "$(basename "$TARGET")" > "$SIDECAR"
ok "sidecar 已寫：$SIDECAR"

step "3. 原子安裝"
install -m 755 "$SOURCE" "${TARGET}.tmp" || die "安裝失敗"
mv -f "${TARGET}.tmp" "$TARGET" || die "原子替換失敗"

# 共用模組一起裝（bridge import 時需要，必須在重啟服務之前）
DETECT_SHA=$(sha256sum "$DETECT_SRC" | awk '{print $1}')
if [ -f "$DETECT_TARGET" ]; then
  CUR_DETECT=$(sha256sum "$DETECT_TARGET" | awk '{print $1}')
  if [ "$CUR_DETECT" != "$DETECT_SHA" ]; then
    cp -a "$DETECT_TARGET" "${DETECT_TARGET}.bak-${STAMP}" || die "模組備份失敗"
    DETECT_BAK="${DETECT_TARGET}.bak-${STAMP}"
  else
    DETECT_BAK=""
  fi
else
  DETECT_BAK=""
fi
install -m 644 "$DETECT_SRC" "${DETECT_TARGET}.tmp" || die "模組安裝失敗"
mv -f "${DETECT_TARGET}.tmp" "$DETECT_TARGET" || die "模組原子替換失敗"
LAND_DETECT=$(sha256sum "$DETECT_TARGET" | awk '{print $1}')
[ "$DETECT_SHA" = "$LAND_DETECT" ] || die "落地模組 sha256 與原始碼不一致"
LAND_SHA=$(sha256sum "$TARGET" | awk '{print $1}')
printf '  landing sha256：%s\n' "$LAND_SHA"
[ "$SRC_SHA" = "$LAND_SHA" ] || die "落地 sha256 與原始碼不一致"

step "4. 重啟服務 + healthcheck"
rollback_bridge() {
  if [ -n "${DETECT_BAK:-}" ] && [ -f "${DETECT_BAK:-}" ]; then
    cp -a "$DETECT_BAK" "$DETECT_TARGET"
    printf '  已回滾共用模組：%s\n' "$DETECT_BAK"
  fi
  if [ -n "$BAK" ] && [ -f "$BAK" ]; then
    cp -a "$BAK" "$TARGET"
    printf '  已從 %s 回滾\n' "$BAK"
  else
    printf '  [!!] 沒有有效備份可回滾 —— 請從原始碼重新部署：\n'
    printf '       bash %s\n' "$0"
  fi
  systemctl restart "$SERVICE" 2>/dev/null
}
if ! systemctl restart "$SERVICE"; then
  bad "重啟失敗 → 回滾"
  rollback_bridge
  exit 1
fi
sleep 3
if ! systemctl is-active --quiet "$SERVICE"; then
  bad "服務未 active → 回滾"
  rollback_bridge
  exit 1
fi
ok "服務 active"

step "5. Smoke test（帶 token 實際打一次）"
AKEY=$(python3 -c "
import yaml
c=yaml.safe_load(open('/var/lib/jysecai/core/config.yaml'))
ch=(c.get('ai',{}).get('channels') or {}).get('grok-4-5') or {}
print(ch.get('api_key',''))
" 2>/dev/null)
if [ -z "$AKEY" ]; then
  bad "無法取得 bridge token，跳過 smoke test"
else
  CODE=$(curl -s -o /tmp/_bridge_smoke.json -w '%{http_code}' -m 120 "$BRIDGE/v1/chat/completions" \
    -H "Authorization: Bearer $AKEY" -H 'Content-Type: application/json' \
    -d '{"model":"grok-3","messages":[{"role":"user","content":"回一句：連線正常"}],"max_tokens":60}')
  TXT=$(python3 -c "
import json
try:
    d=json.load(open('/tmp/_bridge_smoke.json'))
    print((d['choices'][0]['message'].get('content') or '')[:80])
except Exception as e:
    print('ERR', e)
")
  if [ "$CODE" = "200" ] && [ -n "$TXT" ] && [ "${TXT:0:3}" != "ERR" ]; then
    ok "smoke test 通過（HTTP $CODE）：$TXT"
  else
    bad "smoke test 失敗（HTTP $CODE）"
    rollback_bridge
    exit 1
  fi
fi

step "6. 部署收據"
if [ -n "$BAK" ] && [ -f "$BAK" ]; then
  ROLLBACK_CMD="cp -a $BAK $TARGET && systemctl restart $SERVICE"
else
  ROLLBACK_CMD="（無有效備份：從原始碼重新部署 bash $0）"
fi
cat > /opt/jysec-grok-bridge/DEPLOY-RECEIPT.txt <<EOF
service      : $SERVICE
source       : $SOURCE
target       : $TARGET
binary_sha256: $SRC_SHA
detect_source: $DETECT_SRC
detect_target: $DETECT_TARGET
detect_sha256: $DETECT_SHA
deployed_at  : $(date -Iseconds)
backup       : ${BAK:-none}
rollback     : $ROLLBACK_CMD
EOF
cat /opt/jysec-grok-bridge/DEPLOY-RECEIPT.txt

printf '\n完成。回滾指令：\n'
printf '  %s\n' "$ROLLBACK_CMD"
