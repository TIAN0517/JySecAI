#!/bin/bash
# records_pipeline.sh — 記錄資料一鍵流水線
#
# 流程
#   1. 品質閘門（現況）
#   2. 活體提取（可選，需可用出口）→ 產出必須 > 0，否則立刻中止
#   3. 入庫（records-ingest）
#   4. 交付物（限年份窗口）
#   5. 品質閘門（再驗一次）
#
# 為什麼第 2 步一定要 fail-loud
#   2026-11-06 實查：enrich_chailease.py 從未成功寫入任何一筆
#   （member_profile 的 address / loan_amount / periods 全部為 0），
#   當時沒有任何機制報警，缺口就一直潛伏到今天。
#   這支腳本的第 2 步只要產出為 0 就直接中止，不允許「看起來成功」。
#
# 用法
#   bash scripts/records_pipeline.sh                 # 只跑離線步驟（閘門→交付物→閘門）
#   bash scripts/records_pipeline.sh --pull          # 加上活體提取（需出口）
#   bash scripts/records_pipeline.sh --pull --proxy socks5h://user:pass@host:port
#   bash scripts/records_pipeline.sh --years 2023-2026
set -uo pipefail

ROOT=/home/BossJy/JySecAI
DB=/var/lib/jysecai/core/extracted_records.db
AUTH=/var/lib/jysecai/core/records_authorization.json
OUTDIR=/var/lib/jysecai/core/workspace/reports/records-deliverables
INGEST="$ROOT/build/releases/records-ingest"
GATE="$ROOT/scripts/records_quality_gate.py"
YEARS="2023-2026"
DO_PULL=0
PROXY=""
INGEST_FILE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --pull)   DO_PULL=1; shift ;;
    --proxy)  PROXY="$2"; shift 2 ;;
    --years)  YEARS="$2"; shift 2 ;;
    --db)     DB="$2"; shift 2 ;;
    --outdir) OUTDIR="$2"; shift 2 ;;
    --ingest) INGEST_FILE="$2"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "[abort] 未知參數：$1" >&2; exit 2 ;;
  esac
done

step() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
ok()   { printf '  [OK] %s\n' "$*"; }
bad()  { printf '  [!!] %s\n' "$*"; }
die()  { printf '\n[abort] %s\n' "$*" >&2; exit 2; }

step "1/5 品質閘門（現況）"
python3 "$GATE" --db "$DB" --years "$YEARS" || die "品質閘門未達標，先修正再往下"

if [ "$DO_PULL" = "1" ]; then
  step "2/5 活體提取（需要可用出口）"
  PULL_ARGS="--seeds $ROOT/scripts/chailease_seeds.json --outdir /tmp/chailease_pull --workers 4 --delay 0.3"
  [ -n "$PROXY" ] && PULL_ARGS="$PULL_ARGS --proxy $PROXY"
  if ! python3 "$ROOT/scripts/pull_chailease_full.py" $PULL_ARGS; then
    die "活體提取失敗。若是 HTTP 403，代表出口被 Cloudflare WAF 封鎖：
    目前本機（111.68.15.86）與 Windows 側（111.68.15.82）都被 403，
    住宅代理 rp.scrapegw.com:6060 的帳密已失效。
    解阻方式見 scripts/RUNBOOK-CHAILEASE-PULL.md 第 3 節（路徑 B / 路徑 C）。"
  fi

  # ---- 關鍵：產出必須 > 0，否則視為失敗（不允許靜默成功）----
  for f in /tmp/chailease_pull/payload_member_profile.json \
           /tmp/chailease_pull/payload_member_signup.json; do
    [ -f "$f" ] || die "缺少產出檔：$f"
    N=$(python3 -c "
import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8'))
print(len(d if isinstance(d,list) else d.get('records',[])))
" "$f" 2>/dev/null || echo 0)
    if [ "$N" -le 0 ]; then
      bad "$f 產出 0 筆 —— 視為失敗"
      die "活體提取回傳 0 筆。多半是出口被 WAF 403 或 JWT 失效；
      絕不能讓這種情況靜默通過（2026-11-06 的教訓）。"
    fi
    ok "$(basename "$f") 產出 $N 筆"
  done

  step "3/5 入庫（去重鍵命中時就地更新欄位，不新增列）"
  for f in /tmp/chailease_pull/payload_member_profile.json \
           /tmp/chailease_pull/payload_member_signup.json; do
    [ -f "$f" ] || continue
    "$INGEST" --db "$DB" --payload "$f" || die "入庫失敗：$f"
    ok "已入庫 $(basename "$f")"
  done
else
  step "2/5 活體提取：略過（--pull 才執行）"
  step "3/5 入庫：略過"
fi

# ---- 不需網路的手動匯入路徑 ----
# 出口被 WAF 403 封鎖時，仍可由使用者端（能正常開中租網站的機器）跑
# scripts/pull_chailease_full.py，把 payload_member_profile.json /
# payload_member_signup.json 帶回來，用 --ingest 直接入庫。
if [ -n "$INGEST_FILE" ]; then
  step "3b/5 手動匯入（不需網路）"
  [ -f "$INGEST_FILE" ] || die "找不到匯入檔：$INGEST_FILE"
  N=$(python3 -c "
import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8'))
print(len(d if isinstance(d,list) else d.get('records',[])))
" "$INGEST_FILE" 2>/dev/null || echo 0)
  [ "$N" -gt 0 ] || die "匯入檔產出 0 筆，視為失敗（不允許靜默通過）"
  "$INGEST" --db "$DB" --payload "$INGEST_FILE" || die "入庫失敗：$INGEST_FILE"
  ok "已匯入 $INGEST_FILE（$N 筆）"
fi

step "4/5 交付物（年份窗口 $YEARS）"
mkdir -p "$OUTDIR"
python3 "$ROOT/scripts/records_deliverables.py" \
    --db "$DB" --auth "$AUTH" --outdir "$OUTDIR" --years "$YEARS" \
  || die "交付物產生失敗"
ok "交付物 → $OUTDIR"

# 提取記錄總表（含明文個資的工作用總表）。原本這檔沒有任何腳本在產生，
# 是孤兒產物且永遠停在舊版本；接進來才能重現。
XLSX="$OUTDIR/JySecAI-提取記錄總表.xlsx"
python3 "$ROOT/scripts/records_export_xlsx.py" \
    --db "$DB" --out "$XLSX" --years "$YEARS" \
  || die "總表 xlsx 產生失敗"
ok "提取記錄總表 → $XLSX（注意：含明文個資，非對外交付物）"

step "5/5 品質閘門（再驗一次）"
python3 "$GATE" --db "$DB" --years "$YEARS" || die "品質閘門未達標"

printf '\n\033[1m[流水線完成]\033[0m\n'
