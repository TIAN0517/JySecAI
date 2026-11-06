#!/usr/bin/env bash
# 部署 jysec-core，並鎖定「驗證的雜湊」與「落地的雜湊」是同一份。
#
# 為什麼需要這支
#   2026-10-02 實際發生過：守門腳本驗的是 18:46 建置的 98c2e8b6...（103,789,225 bytes），
#   但 /opt 上落地跑的是 19:11 又重編譯的 1ed27000...（106,174,704 bytes）。
#   守門條件形同虛設。本流程在建置後立刻封存 sha256，部署前後都拿它當唯一事實來源。
#
# 核心保證
#   1. 不重建。腳本永遠不會自己 go build，只搬你指定的二進位。
#   2. 搬之前先驗 source == sidecar；sidecar 是建置當下寫下的唯一真相。
#   3. 先寫到 target.tmp 再 mv 原子替換，落地後立刻重算落地檔 sha256 必須三者一致。
#   4. 任一步失敗自動從時間戳備份還原並重啟服務。
#   5. 寫一份部署收據，之後可以證明「驗了什麼、跑了什麼」。
#
# 用法
#   # 正常部署
#   sudo bash deploy-jysec-core.sh \
#     --binary  /mnt/c/.../jysec-core-linux \
#     --sidecar /mnt/c/.../jysec-core-linux.sha256 \
#     --target  /opt/jysecai/core/current/jysec-core \
#     --service jysec-core \
#     --healthcheck /usr/local/sbin/jysec-healthcheck
#
#   # 只驗證不安裝
#   sudo bash deploy-jysec-core.sh --binary ... --sidecar ... --target ... --verify-only
#
#   # 不需要 root 的自我測試
#   bash deploy-jysec-core.sh --self-test

set -uo pipefail

BINARY=""; SIDECAR=""; TARGET=""; SERVICE=""; HEALTHCHECK=""
VERIFY_ONLY=0; SELF_TEST=0

die()  { printf '\n[abort] %s\n' "$*" >&2; exit 2; }
step() { printf '\n== %s ==\n' "$*"; }
ok()   { printf '  [OK] %s\n' "$*"; }
bad()  { printf '  [!!] %s\n' "$*"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --binary)      BINARY="$2"; shift 2 ;;
    --sidecar)     SIDECAR="$2"; shift 2 ;;
    --target)      TARGET="$2"; shift 2 ;;
    --service)     SERVICE="$2"; shift 2 ;;
    --healthcheck) HEALTHCHECK="$2"; shift 2 ;;
    --verify-only)  VERIFY_ONLY=1; shift ;;
    --self-test)    SELF_TEST=1; shift ;;
    -h|--help)     sed -n '2,30p' "$0"; exit 0 ;;
    *) die "未知參數：$1" ;;
  esac
done

sha_of() { sha256sum "$1" | awk '{print $1}'; }
size_of() { wc -c < "$1" | tr -d ' '; }

# 從 sidecar 取出雜湊，容忍 "<hash>  <file>" 或純 hash 兩種格式
sidecar_hash() {
  awk 'NF {print $1; exit}' "$1"
}

read_sidecar_hash() {
  [ -f "$SIDECAR" ] || die "找不到 sidecar：$SIDECAR
（建置後請執行：sha256sum $(basename "$BINARY") > $(basename "$BINARY").sha256）"
  local h
  h="$(sidecar_hash "$SIDECAR")"
  case "$h" in
    [0-9a-f][0-9a-f]*) [ "${#h}" -eq 64 ] || die "sidecar 內容不像 sha256：$h" ;;
    *) die "sidecar 第一個 token 不是 64 碼 hex：$h" ;;
  esac
  printf '%s' "$h"
}

restore_and_die() {
  local backup="$1" why="$2"
  bad "$why"
  if [ -n "$backup" ] && [ -f "$backup" ]; then
    bad "從備份還原：$backup"
    cp -p "$backup" "$TARGET"
    if [ -n "$SERVICE" ]; then
      systemctl restart "$SERVICE" && bad "已重啟 $SERVICE（回滾完成）" || bad "重啟 $SERVICE 失敗，請手動處理"
    fi
  fi
  die "部署失敗，已回到操作前狀態"
}

# ---------------------------------------------------------------- self test
if [ "$SELF_TEST" -eq 1 ]; then
  step "self-test：模擬 source / sidecar / target 三方雜湊比對"
  T="$(mktemp -d)"
  trap 'rm -rf "$T"' EXIT
  head -c 4096 /dev/urandom > "$T/jysec-core"
  sha256sum "$T/jysec-core" | awk '{print $1"  jysec-core"}' > "$T/jysec-core.sha256"

  EXPECT="$(sidecar_hash "$T/jysec-core.sha256")"
  ACTUAL="$(sha_of "$T/jysec-core")"
  [ "$EXPECT" = "$ACTUAL" ] && ok "sidecar 與 source 一致" || die "self-test：一致時卻判定不符"

  printf 'tampered' >> "$T/jysec-core"
  TAMPERED="$(sha_of "$T/jysec-core")"
  [ "$EXPECT" != "$TAMPERED" ] && ok "竄改後被辨識（source 雜湊已變）" || die "self-test：竄改後竟判定相同"
  # 這正是 2026-10-02 真正的失效模式：sidecar 與實際要搬的檔案已經不是同一份
  bad "-> 正式流程會在搬運前就中止"

  cp "$T/jysec-core" "$T/target"
  LANDED="$(sha_of "$T/target")"
  [ "$TAMPERED" = "$LANDED" ] && ok "落地檔雜湊與搬運來源一致" || die "self-test：落地不一致"

  rm -f "$T/target"
  if [ -f "$T/target" ]; then bad "刪除失敗"; else ok "清理正常"; fi
  printf '\n[self-test] 全部通過\n'
  exit 0
fi

# ---------------------------------------------------------------- real run
[ -n "$BINARY" ] && [ -n "$SIDECAR" ] && [ -n "$TARGET" ] || \
  die "需要 --binary / --sidecar / --target"

[ -f "$BINARY" ] || die "找不到來源二進位：$BINARY"

step "1/6 驗證來源與 sidecar"
EXPECT="$(read_sidecar_hash)"
ACTUAL="$(sha_of "$BINARY")"
printf '  sidecar : %s\n' "$EXPECT"
printf '  source  : %s  (%s bytes)\n' "$ACTUAL" "$(size_of "$BINARY")"
if [ "$EXPECT" != "$ACTUAL" ]; then
  die "來源二進位與 sidecar 不符。
這代表建置之後又被重新編譯過 —— 正是 2026-10-02 守門失效的原因。
請重新建置並重新產生 sidecar，不要略過這一步。"
fi
ok "來源 == sidecar"

if [ "$VERIFY_ONLY" -eq 1 ]; then
  step "verify-only：檢查目前落地檔"
  if [ -f "$TARGET" ]; then
    CUR="$(sha_of "$TARGET")"
    printf '  目前落地 : %s  (%s bytes)\n' "$CUR" "$(size_of "$TARGET")"
    if [ "$CUR" = "$EXPECT" ]; then ok "落地檔已是同一份"; else bad "落地檔與 sidecar 不同（尚未部署）"; fi
  else
    bad "落地檔不存在：$TARGET"
  fi
  exit 0
fi

[ -f "$TARGET" ] || die "落地目標不存在：$TARGET（這支腳本只做替換，不做首次安裝）"

CUR_BEFORE="$(sha_of "$TARGET")"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="${TARGET}.bak-${STAMP}"
cp -p "$TARGET" "$BACKUP"
ok "已備份現行版本 → $BACKUP"

step "2/6 原子替換落地檔"
# 2026-10-03 教訓：只驗雜湊不夠。用 cp 從 Windows 掛載點(/mnt/c)搬過來時，檔案 mode
# 不可靠地被帶成非可執行，systemd 直接 203/EXEC 開不起來 —— 雜湊是對的，服務照樣死。
# 改用 install 明確指定 mode 與 owner，並在碰 systemd 之前先驗「可執行」與「可讀」。
OWNER_U="$(stat -c '%U' "$TARGET" 2>/dev/null || echo root)"
OWNER_G="$(stat -c '%G' "$TARGET" 2>/dev/null || echo root)"
MODE="$(stat -c '%a' "$TARGET" 2>/dev/null || echo 755)"

if ! install -m "$MODE" -o "$OWNER_U" -g "$OWNER_G" "$BINARY" "${TARGET}.new.$$"; then
  die "install 失敗，目標檔未動"
fi
# 保底：安裝過程若遺漏執行位元，這裡一定補上
chmod u+x,g+x,o+x "${TARGET}.new.$$" || { rm -f "${TARGET}.new.$$"; die "無法設定執行位元"; }
chmod u+r "${TARGET}.new.$$" || { rm -f "${TARGET}.new.$$"; die "無法設定讀取位元"; }

[ -r "${TARGET}.new.$$" ] || { rm -f "${TARGET}.new.$$"; die "暫存檔不可讀"; }
[ -x "${TARGET}.new.$$" ] || { rm -f "${TARGET}.new.$$"; die "暫存檔不可執行（這正是上次 203/EXEC 的原因）"; }
printf '  權限   : %s owner=%s:%s\n' "$(stat -c '%a' "${TARGET}.new.$$")" "$OWNER_U" "$OWNER_G"

mv -f "${TARGET}.new.$$" "$TARGET" || { rm -f "${TARGET}.new.$$"; restore_and_die "$BACKUP" "原子替換失敗"; }
ok "已替換"

step "3/6 驗證落地後的實際檔案"
LANDED="$(sha_of "$TARGET")"
printf '  落地檔 : %s  (%s bytes, mode %s)\n' "$LANDED" "$(size_of "$TARGET")" "$(stat -c '%a' "$TARGET")"
[ "$LANDED" = "$EXPECT" ] || restore_and_die "$BACKUP" "落地後雜湊與 sidecar 不符（$LANDED != $EXPECT）"
ok "落地 == sidecar == source，三方一致"
# 雜湊對了還不夠：這一步是上次真正缺的那個閘門
[ -r "$TARGET" ] || restore_and_die "$BACKUP" "落地檔不可讀"
[ -x "$TARGET" ] || restore_and_die "$BACKUP" "落地檔不可執行（systemd 會 203/EXEC）"
ok "落地檔可讀且可執行（systemd 203 的預防閘門）"

step "4/6 寫部署收據"
RECEIPT="${TARGET}.deploy-receipt.json"
cat > "$RECEIPT" <<EOF
{
  "deployed_at": "$(date -Is)",
  "sha256": "$LANDED",
  "bytes": $(size_of "$TARGET"),
  "source_path": "$BINARY",
  "target_path": "$TARGET",
  "backup_path": "$BACKUP",
  "previous_sha256": "$CUR_BEFORE"
}
EOF
ok "收據 → $RECEIPT"

if [ -n "$SERVICE" ]; then
  step "5/6 重啟 $SERVICE"
  if ! systemctl restart "$SERVICE"; then
    restore_and_die "$BACKUP" "systemctl restart $SERVICE 失敗"
  fi
  sleep 2
  systemctl is-active --quiet "$SERVICE" \
    && ok "$SERVICE active" \
    || restore_and_die "$BACKUP" "$SERVICE 重啟後不是 active"
else
  step "5/6 略過（未指定 --service）"
fi

if [ -n "$HEALTHCHECK" ] && [ -x "$HEALTHCHECK" ]; then
  step "6/6 healthcheck"
  if "$HEALTHCHECK"; then
    ok "healthcheck 通過"
  else
    restore_and_die "$BACKUP" "healthcheck 未通過"
  fi
else
  step "6/6 略過（未指定 --healthcheck 或不可執行）"
fi

printf '\n[部署完成] sha256=%s\n' "$LANDED"
printf '  回滾指令：cp -p %s %s && systemctl restart %s\n' "$BACKUP" "$TARGET" "${SERVICE:-<service>}"
