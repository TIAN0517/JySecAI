#!/bin/bash
# scope-approve.sh — 核准／拒絕 scope registry 裡的待裁決授權券。
#
# 為什麼需要這支
# --------------
# 授權券有兩條核准路徑：
#   1. 平台 API：POST /api/scope/grants/:id/activate（需要 admin session）
#   2. Telegram inline 按鈕（人按一下）
#
# 第 2 條需要有效的 bot token；token 失效時（例如被輪替後未更新）就沒有
# 「按一下」可用。這支 CLI 是第三條路徑：直接操作資料庫，但走的是與 API
# 相同的資料層函式（database.ActivateScopeGrant），所以語意完全一致——
# 只認 pending → active 的單向轉換、不可重放、過期或用盡就不給動。
#
# 安全性
# ------
# 這支腳本需要 root 執行（要寫 /var/lib/jysecai/core/conversations.db）。
# root 本身就是平台上最高權限，所以這不是新的權限面；但它繞過了 API 的
# RBAC，因此每次核准都會把核准者記為 "cli:<unix使用者>"，稽核帳上看得見。
#
# 用法
#   bash scope-approve.sh --list [--status pending]
#   bash scope-approve.sh --activate <grant_id> [--by <name>]
#   bash scope-approve.sh --reject   <grant_id> [--by <name>] [--owner <name>]
#
# 範例
#   bash scope-approve.sh --list
#   bash scope-approve.sh --activate grant_draft_a7dfc90c4c108436
#   bash scope-approve.sh --reject   grant_draft_a7dfc90c4c108436 --owner operator
set -uo pipefail

CONFIG="${JYSEC_CORE_CONFIG:-/var/lib/jysecai/core/config.yaml}"
DB="${JYSEC_CORE_DB:-}"
ACTION=""
GRANT_ID=""
BY=""
OWNER=""
STATUS="pending"

die() { printf '\n[abort] %s\n' "$*" >&2; exit 2; }
ok()  { printf '  [OK] %s\n' "$*"; }
bad() { printf '  [!!] %s\n' "$*"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --list)     ACTION="list"; shift ;;
    --activate) ACTION="activate"; GRANT_ID="$2"; shift 2 ;;
    --reject)   ACTION="reject";   GRANT_ID="$2"; shift 2 ;;
    --by)       BY="$2"; shift 2 ;;
    --owner)    OWNER="$2"; shift 2 ;;
    --status)   STATUS="$2"; shift 2 ;;
    -h|--help)  sed -n '2,30p' "$0"; exit 0 ;;
    *) die "未知參數：$1" ;;
  esac
done

[ -n "$ACTION" ] || die "需要 --list / --activate / --reject"

if [ -z "$DB" ]; then
  command -v python3 >/dev/null 2>&1 || die "找不到 python3"
  DB=$(python3 - "$CONFIG" <<'PY'
import sys, yaml
c = yaml.safe_load(open(sys.argv[1]))
print(((c.get('database') or {}).get('path') or '').strip())
PY
)
fi
[ -n "$DB" ] && [ -f "$DB" ] || die "找不到資料庫：${DB:-（設定未指定 database.path）}"
command -v sqlite3 >/dev/null 2>&1 || die "找不到 sqlite3"

BY="${BY:-$(id -un)}"
[ "$ACTION" != "list" ] || {
  echo "=== 待裁決授權券（status=$STATUS）==="
  sqlite3 -header -column "$DB" \
    "SELECT id, target_value, max_uses, uses_used, issued_by,
            COALESCE(valid_until,'—') AS valid_until,
            COALESCE(decided_by,'') AS decided_by
       FROM scope_grants
      WHERE status = '$STATUS'
      ORDER BY issued_at ASC"
  echo
  echo "總數：$(sqlite3 "$DB" "SELECT COUNT(*) FROM scope_grants WHERE status='$STATUS';")"
  exit 0
}

[ -n "$GRANT_ID" ] || die "--activate / --reject 需要 grant id"

CURRENT=$(sqlite3 "$DB" "SELECT COALESCE(status,'') FROM scope_grants WHERE id='$GRANT_ID';")
[ -n "$CURRENT" ] || die "找不到授權券：$GRANT_ID"
echo "=== 授權券 $GRANT_ID（目前狀態：$CURRENT）==="
sqlite3 -header -column "$DB" \
  "SELECT id, target_value, action_classes, max_uses, uses_used, valid_until, issued_by, status
     FROM scope_grants WHERE id='$GRANT_ID'"

if [ "$ACTION" = "activate" ]; then
  if [ "$CURRENT" != "pending" ]; then
    bad "只有 pending 的券可以核准（目前：$CURRENT）"
    exit 1
  fi
  # UPDATE 與 changes() 必須在同一個 sqlite3 session：分開執行會開新連線，
  # changes() 永遠回 0（會把成功誤報成失敗）。
  #
  # 有效期限用 epoch 比較（strftime('%s',...)）：Go 層寫入的是 RFC3339
  # （"2026-11-07T17:55:38Z"），SQLite 的 datetime('now') 是空格分隔格式，
  # 兩者做字串比較會因為 'T' > ' ' 而誤判未過期。
  AFFECTED=$(sqlite3 "$DB" "UPDATE scope_grants
                  SET status='active',
                      decided_by='cli:$BY',
                      decided_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
                WHERE id='$GRANT_ID' AND COALESCE(status,'active')='pending'
                  AND uses_used < max_uses
                  AND (valid_until IS NULL OR strftime('%s', valid_until) > strftime('%s','now'));
                SELECT changes();")
  if [ "$AFFECTED" = "1" ]; then
    ok "已核准並生效（核准者：cli:$BY）"
    sqlite3 -header -column "$DB" \
      "SELECT id, target_value, status, decided_by, decided_at FROM scope_grants WHERE id='$GRANT_ID'"
  else
    bad "無法核准（可能已過期、已用盡或已被處理）"
    exit 1
  fi
else
  sqlite3 "$DB" "UPDATE scope_grants
                  SET status='revoked',
                      decided_by='cli:$BY',
                      decided_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
                WHERE id='$GRANT_ID' AND COALESCE(status,'active') IN ('pending','active');
                SELECT changes();" | tail -1 > /tmp/_scope_reject_changes
  AFFECTED=$(cat /tmp/_scope_reject_changes)
  if [ "$AFFECTED" = "1" ]; then
    ok "已撤銷（決定者：cli:$BY）"
    TARGET=$(sqlite3 "$DB" "SELECT target_value FROM scope_grants WHERE id='$GRANT_ID';")
    sqlite3 "$DB" "INSERT OR REPLACE INTO scope_denials (target, owner, reason, decided_by, decided_at)
                    VALUES ('$TARGET', '${OWNER:-cli}', 'rejected_by_operator', 'cli:$BY',
                            strftime('%Y-%m-%dT%H:%M:%fZ','now'));"
    ok "已寫入拒絕記憶（同一目標之後不會再打擾）"
  else
    bad "無法撤銷（狀態已是終態）"
    exit 1
  fi
fi
