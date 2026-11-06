#!/bin/bash
# verify_release.sh — 發佈前複查複測（0 bug 門禁）
#
# 檢查項目
#   1  服務狀態與 healthcheck
#   2  部署收據：source sha == sidecar == 落地 sha
#   3  web 資產與原始碼逐檔一致（執行時是從磁碟讀 web/，不同步等於沒部署）
#   4  記錄庫完整性：筆數、型別數、去重（重複列必須為 0）
#   5  records API：types（欄位有值率）、list（排序 + 注入防護）、classification、export
#   6  scan-runner 功能測試（併發 / 次數上限 / DNS 路徑 / 錯誤不中斷）
#   7  AI 連線：grok 通道可用
#   8  AI developer mode：注入開 → 不得拒絕；注入關 → 應拒絕（證明是提示詞在改變行為）
#   9  平台對話端到端：/api/eino-agent 真的能產出回答
#
# 全部通過 → exit 0；任一失敗 → exit 1（並在最後列出失敗項）
set -uo pipefail

ROOT=/home/BossJy/JySecAI
RECORDS=/var/lib/jysecai/core/extracted_records.db
API=http://127.0.0.1:9898
BRIDGE=http://127.0.0.1:18788
AUTH=/var/lib/jysecai/core/records_authorization.json
CONVDB=/var/lib/jysecai/core/conversations.db
PASS=0; FAIL=0; FAILED=()

ok()   { PASS=$((PASS+1)); printf '  \033[32mPASS\033[0m  %s\n' "$1"; }
bad()  { FAIL=$((FAIL+1)); FAILED+=("$1"); printf '  \033[31mFAIL\033[0m  %s\n' "$1"; [ -n "${2:-}" ] && printf '        %s\n' "$2"; }
sect() { printf '\n=== %s ===\n' "$1"; }

# ---------------------------------------------------------------- 1 服務
sect "1. 服務狀態"
if systemctl is-active --quiet jysec-core; then ok "jysec-core active"; else bad "jysec-core active" "$(systemctl status jysec-core --no-pager | tail -3)"; fi
if /usr/local/sbin/jysec-healthcheck >/dev/null 2>&1; then ok "healthcheck 通過"; else bad "healthcheck 通過"; fi
if systemctl is-active --quiet jysec-grok-bridge; then ok "jysec-grok-bridge active"; else bad "jysec-grok-bridge active"; fi

# ---------------------------------------------------------------- 2 收據
sect "2. 部署收據（三方 sha256 一致）"
SRC_SHA=$(sha256sum "$ROOT/build/releases/jysec-core" | awk '{print $1}')
SIDE_SHA=$(awk '{print $1}' "$ROOT/build/releases/jysec-core.sha256" 2>/dev/null)
LAND_SHA=$(sha256sum /opt/jysecai/core/current/jysec-core 2>/dev/null | awk '{print $1}')
if [ -n "$SRC_SHA" ] && [ "$SRC_SHA" = "$SIDE_SHA" ] && [ "$SRC_SHA" = "$LAND_SHA" ]; then
  ok "source == sidecar == landing（${SRC_SHA:0:12}…）"
else
  bad "source == sidecar == landing" "src=${SRC_SHA:0:12} side=${SIDE_SHA:0:12} land=${LAND_SHA:0:12}"
fi

# 2026-11-06：落地二進位與其所在的 release 目錄，必須不是服務帳號（jysec）可寫。
# 為什麼要查「目錄」而不只是檔案 mode：檔案 chmod 600 也擋不住 unlink ——
# 能替換檔案的是「父目錄的寫入權」。服務帳號若能改寫自己執行的二進位，
# 等於拿到跨重啟的持久化；而 sha256 只證明「部署當下」一致，證明不了事後沒被改。
LANDBIN=/opt/jysecai/core/current/jysec-core
# release 目錄本身（不是它的上一層 releases/）—— 能被 unlink 的是這一層。
LANDDIR=$(readlink -f /opt/jysecai/core/current)
# _jysec_w 成功（exit 0）代表該路徑對 jysec 可寫。
_jysec_w() {
  if command -v runuser >/dev/null 2>&1; then
    runuser -u jysec -- test -w "$1" >/dev/null 2>&1
  else
    su -s /bin/sh -c "test -w '$1'" jysec >/dev/null 2>&1
  fi
}
BINW=0; DIRW=0
_jysec_w "$LANDBIN" && BINW=1
_jysec_w "$LANDDIR" && DIRW=1
if [ "$BINW" = "0" ] && [ "$DIRW" = "0" ]; then
  ok "落地二進位與 release 目錄皆非服務帳號可寫"
else
  bad "落地二進位權限" "jysec 可寫二進位=$BINW 可寫目錄=$DIRW（$LANDDIR）"
fi

# 2026-11-06：systemd unit 檔不得含明文機密（FOFA/ZoomEye 等金鑰）。
# 原始情況：drop-in 是 644，任何本機帳號都能讀到金鑰。應改用 EnvironmentFile（0600 root）。
if grep -qsE 'Environment=[A-Za-z_]*(API_KEY|SECRET|PASSWORD|TOKEN)=.+' \
     /etc/systemd/system/jysec-core.service \
     /etc/systemd/system/jysec-core.service.d/*.conf 2>/dev/null; then
  bad "unit 檔含明文機密" "應改用 EnvironmentFile（0600 root）"
else
  ok "unit 檔不含明文機密"
fi

# bridge 也要有收據。原因：2026-11-06 實查發現 dev-mode 實作只存在於落地檔，
# 原始碼從未同步 —— 從原始碼重建就會弄丟，而沒有任何檢查會發現。
BR_SRC=$(sha256sum "$ROOT/tools/grok_openai_bridge_slim.py" 2>/dev/null | awk '{print $1}')
BR_SIDE=$(awk '{print $1}' /opt/jysec-grok-bridge/grok_openai_bridge_slim.py.sha256 2>/dev/null)
BR_LAND=$(sha256sum /opt/jysec-grok-bridge/grok_openai_bridge_slim.py 2>/dev/null | awk '{print $1}')
if [ -n "$BR_SRC" ] && [ "$BR_SRC" = "$BR_SIDE" ] && [ "$BR_SRC" = "$BR_LAND" ]; then
  ok "bridge source == sidecar == landing（${BR_SRC:0:12}…）"
else
  bad "bridge source == sidecar == landing" "src=${BR_SRC:0:12} side=${BR_SIDE:0:12} land=${BR_LAND:0:12}"
fi
# bridge 的拒絕偵測必須跟 verify 共用同一份實作，否則兩邊會漂移
# （2026-11-06 實測：兩邊都漏接 "No." / "**Refused.**" 造成假通過）。
if cmp -s "$ROOT/scripts/_refusal_detect.py" /opt/jysec-grok-bridge/_refusal_detect.py; then
  ok "bridge 與 verify 共用同一份拒絕偵測模組"
else
  bad "bridge 與 verify 共用同一份拒絕偵測模組" "scripts/_refusal_detect.py 與 /opt/jysec-grok-bridge/_refusal_detect.py 不一致"
fi
# 拒絕偵測的行為必須被釘住：有誤判（把正常句子當拒絕）會讓對照組假通過。
if python3 "$ROOT/scripts/_refusal_detect.py" --selftest >/dev/null 2>&1; then
  ok "拒絕偵測模組自我測試通過"
else
  bad "拒絕偵測模組自我測試" "_refusal_detect.py --selftest 有樣本不符"
fi

# ---------------------------------------------------------------- 3 web 資產
sect "3. web 資產與原始碼一致"
MIS=0; CNT=0
while IFS= read -r f; do
  rel="${f#$ROOT/web/}"
  [ -f "/opt/jysecai/core/current/web/$rel" ] || continue
  CNT=$((CNT+1))
  a=$(sha256sum "$f" | awk '{print $1}')
  b=$(sha256sum "/opt/jysecai/core/current/web/$rel" | awk '{print $1}')
  [ "$a" = "$b" ] || { MIS=$((MIS+1)); echo "        不一致: $rel"; }
done < <(find "$ROOT/web" -type f)
if [ "$MIS" -eq 0 ]; then ok "$CNT 個 web 檔案全部一致"; else bad "web 資產一致" "$MIS 個不一致"; fi

# 反向比對：落地目錄不該出現原始碼沒有的檔案。
# 2026-11-06：原腳本只比對 source -> landing，落地側多出的殘留檔完全不會被發現。
# 實例：XSS 截圖模組的 html2canvas 只存在於落地目錄、原始碼沒有 —— 乾淨重建即斷。
EX=0
while IFS= read -r f; do
  rel="${f#/opt/jysecai/core/current/web/}"
  [ -f "$ROOT/web/$rel" ] || { echo "        落地多出: $rel"; EX=$((EX+1)); }
done < <(find /opt/jysecai/core/current/web -type f)
if [ "$EX" -eq 0 ]; then ok "落地目錄無原始碼以外的多餘檔案"; else bad "落地多餘檔案" "$EX 個落地側多餘檔"; fi
CSSN=$(curl -s "$API/" -m 20 | grep -c 'css/records.css')
JSN=$(curl -s "$API/" -m 20 | grep -c 'js/records.js')
if [ "$CSSN" = "1" ] && [ "$JSN" = "1" ]; then ok "index.html 資產各只引用一次"; else bad "index.html 資產引用" "css=$CSSN js=$JSN"; fi

# ---------------------------------------------------------------- 4 記錄庫
sect "4. 記錄庫完整性"
TOT=$(sqlite3 "$RECORDS" "SELECT COUNT(*) FROM records;")
DUP=$(sqlite3 "$RECORDS" "SELECT COUNT(*) - COUNT(DISTINCT type_id || char(124) || dataset || char(124) || dedupe_key) FROM records;")
NTY=$(sqlite3 "$RECORDS" "SELECT COUNT(DISTINCT type_id) FROM records;")
if [ "$DUP" = "0" ]; then ok "去重：重複列 = 0（總筆數 $TOT）"; else bad "去重：重複列 = $DUP"; fi
if [ "$NTY" -ge 9 ]; then ok "有資料的型別數 = $NTY"; else bad "型別數" "$NTY"; fi
EMPTY=$(sqlite3 "$RECORDS" "SELECT COUNT(*) FROM records;")
if [ "$EMPTY" -gt 0 ]; then ok "記錄庫非空"; else bad "記錄庫非空"; fi

# ---------------------------------------------------------------- 5 API
# ---------------------------------------------------------------- 4b 品質閘門
sect "4b. 資料品質閘門（欄位填值率 + 年份窗口）"
# 為什麼要這組：原本第 4 組只驗「去重 0 筆重複」與「有資料型別 N 個」，
# 這兩件事都跟欄位有沒有值無關。實測發現 member_profile 4353 筆的
# name/id_number/address 全部不存在、loan_case 的 address 只有 1 筆有值，
# 舊閘門完全查不出來。
RQ_LOG=/tmp/_jysec_records_quality.log
if python3 "$ROOT/scripts/records_quality_gate.py" \
     --db /var/lib/jysecai/core/extracted_records.db --years 2023-2026 \
     > "$RQ_LOG" 2>&1; then
  ok "欄位填值率 + 年份窗口 達標"
else
  bad "欄位填值率 + 年份窗口" "詳見 $RQ_LOG"
  grep -E "FAIL" "$RQ_LOG" | sed 's/^/        /'
fi
# 需求欄位覆蓋（姓名/電話/描述/地址/身份證/貸款日期）—— 持續可見，不阻擋發佈
sed -n "/■ 需求欄位覆蓋/,/■ 判定/p" "$RQ_LOG" | sed 's/^/      /'

sect "5. records API"
U=verify_rel_tmp
P="Tmp$(head -c 10 /dev/urandom | base64 | tr -dc 'A-Za-z0-9')"
HASH=$(CHAILEASE="$P" python3 -c "import bcrypt,os;print(bcrypt.hashpw(os.environ['CHAILEASE'].encode(), bcrypt.gensalt(rounds=10)).decode())")
sqlite3 "$CONVDB" "INSERT OR REPLACE INTO rbac_users (id,username,display_name,password_hash,enabled,is_builtin,created_at,updated_at) VALUES ('verify-rel-001','$U','臨時','$HASH',1,0,datetime('now'),datetime('now'));"
sqlite3 "$CONVDB" "INSERT OR REPLACE INTO rbac_user_roles (user_id,role_id,created_at) VALUES ('verify-rel-001','admin',datetime('now'));"
TOKEN=$(curl -s -X POST "$API/api/auth/login" -H 'Content-Type: application/json' \
  -d "{\"username\":\"$U\",\"password\":\"$P\"}" -m 20 | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))")
if [ -n "$TOKEN" ]; then ok "登入取得 token"; else bad "登入取得 token"; fi
AH=(-H "Authorization: Bearer $TOKEN")

TYPES=$(curl -s "${AH[@]}" -m 60 "$API/api/records/types")
echo "$TYPES" | python3 -c "
import sys,json
d=json.load(sys.stdin)
n=len([t for t in d['types'] if t['count']])
fill=sum(1 for t in d['types'] if t.get('fill') is not None)
print('%d %d %d' % (d['total'], n, fill))
" > /tmp/_t.txt
read -r T_TOTAL T_WITH T_FILL < /tmp/_t.txt
if [ "$T_TOTAL" -gt 0 ]; then ok "types：總筆數 $T_TOTAL，有資料型別 $T_WITH"; else bad "types 總筆數"; fi
if [ "$T_FILL" -gt 0 ]; then ok "types：欄位有值率已回傳（$T_FILL 個型別）"; else bad "types 欄位有值率"; fi

SORTED=$(curl -s "${AH[@]}" -m 60 "$API/api/records/list?type=loan_case_master&page=1&page_size=5&sort_by=first_apply_at&sort_dir=desc")
echo "$SORTED" | python3 -c "
import sys,json
d=json.load(sys.stdin)
ds=[i['fields'].get('first_apply_at','') for i in d['items']]
okk = ds == sorted(ds, reverse=True) and len([x for x in ds if x])>=3
print('yes' if okk else 'no', ds[:2])
" > /tmp/_s.txt
if grep -q '^yes' /tmp/_s.txt; then ok "list：依日期欄位 desc 排序正確"; else bad "list 排序" "$(cat /tmp/_s.txt)"; fi

BASE_TOTAL=$(curl -s "${AH[@]}" -m 60 "$API/api/records/list?type=loan_case_master&page=1&page_size=1" | python3 -c "import sys,json;print(json.load(sys.stdin).get('total',0))")
INJ=$(curl -s "${AH[@]}" -m 60 "$API/api/records/list?type=loan_case_master&page=1&page_size=2&sort_by=case_no%3B%20DROP%20TABLE%20records&sort_dir=desc" | python3 -c "import sys,json;print(json.load(sys.stdin).get('total',0))")
ALIVE=$(sqlite3 "$RECORDS" "SELECT COUNT(*) FROM records;")
if [ "$INJ" = "$BASE_TOTAL" ] && [ "$ALIVE" = "$TOT" ]; then
  ok "list：注入字串被忽略（回應筆數不變 $INJ），資料表完好（$ALIVE 筆）"
else
  bad "注入防護" "base=$BASE_TOTAL inj=$INJ db=$ALIVE expect_db=$TOT"
fi

CLS=$(curl -s "${AH[@]}" -m 60 "$API/api/records/classification?type=loan_application" | python3 -c "import sys,json;print(len(json.load(sys.stdin).get('buckets') or []))")
if [ "$CLS" -gt 0 ]; then ok "classification：$CLS 個分類桶"; else bad "classification"; fi

EXP=$(curl -s "${AH[@]}" -o /tmp/_exp.csv -w '%{http_code}' -m 90 "$API/api/records/export?type=loan_application")
BYTES=$(stat -c %s /tmp/_exp.csv 2>/dev/null || echo 0)
if [ "$EXP" = "200" ] && [ "$BYTES" -gt 1000 ]; then ok "export：HTTP 200，$BYTES bytes"; else bad "export" "http=$EXP bytes=$BYTES"; fi

# ---------------------------------------------------------------- 6 scan-runner
sect "6. scan-runner 功能測試"
if [ -x "$ROOT/build/releases/scan-runner" ]; then
  ok "scan-runner 存在"
  rm -rf /tmp/_scan_t && mkdir -p /tmp/_scan_t/www && cd /tmp/_scan_t/www
  echo '<html><title>t</title></html>' > index.html
  python3 -m http.server 8098 --bind 127.0.0.1 >/dev/null 2>&1 &
  HP=$!; sleep 2; cd - >/dev/null
  "$ROOT/build/releases/scan-runner" --url http://127.0.0.1:8098/ --paths /index.html,/a.html,/b.html \
     --concurrency 3 --max-requests 7 --out /tmp/_scan_t/out >/dev/null 2>&1
  N=$(wc -l < /tmp/_scan_t/out/scan_raw.jsonl 2>/dev/null || echo 0)
  RS=$(grep -o 'max_requests\|max_duration\|task_queue_exhausted' /tmp/_scan_t/out/scan_report.md 2>/dev/null | head -1)
  if [ "$N" = "7" ] && [ "$RS" = "max_requests" ]; then ok "併發掃描精確停在次數上限（7 次 / $RS）"; else bad "scan-runner 次數上限" "n=$N stop=$RS"; fi
  kill $HP 2>/dev/null
else
  bad "scan-runner 存在"
fi

# ---------------------------------------------------------------- 7 AI 連線
sect "7. AI 連線（grok 通道）"
AKEY=$(python3 -c "
import yaml
c=yaml.safe_load(open('/var/lib/jysecai/core/config.yaml'))
ch=(c.get('ai',{}).get('channels') or {}).get('grok-4-5') or {}
print(ch.get('api_key',''))
")
GROKCODE=$(curl -s -o /tmp/_grok.json -w '%{http_code}' -m 120 "$BRIDGE/v1/chat/completions" \
  -H "Authorization: Bearer $AKEY" -H 'Content-Type: application/json' \
  -d '{"model":"grok-3","messages":[{"role":"user","content":"回一句：連線正常"}],"max_tokens":100}')
GROKTXT=$(python3 -c "
import json
try:
    d=json.load(open('/tmp/_grok.json'))
    print((d['choices'][0]['message'].get('content') or '')[:80])
except Exception as e:
    print('ERR', e)
")
if [ "$GROKCODE" = "200" ] && [ -n "$GROKTXT" ]; then ok "grok-3 通道可用（HTTP 200）"; else bad "grok-3 通道" "http=$GROKCODE"; fi

# developer mode 的主機端開關狀態。JYSEAI_DEV_MODE=off 時 bridge 不注入
# dev-mode 提示詞；這裡把實際生效的狀態講清楚，避免「以為開著其實關著」。
DEVMODE_ENV=$(grep -oP '(?<=^JYSEAI_DEV_MODE=).*' /etc/jysecai/grok-bridge.env 2>/dev/null | head -1)
if [ -z "$DEVMODE_ENV" ]; then
  ok "developer mode 主機端開關：預設 on（bridge 未設定 JYSEAI_DEV_MODE）"
else
  ok "developer mode 主機端開關：JYSEAI_DEV_MODE=$DEVMODE_ENV"
fi

# ---------------------------------------------------------------- 8 dev-mode
sect "8. developer mode（注入開／關對照）"
# 驗收元件放在 scripts/_verify_devmode.py，原因：
#   · 拒絕偵測要跟 bridge 共用 scripts/_refusal_detect.py（兩邊各寫一份會漂移）
#   · 上游 xAI 的安全判定是隨機的，單次抽樣會讓門禁隨機紅燈 → 取樣 N 次全中才算
#   · 要帶工具才是平台的真實生產形狀（agent 一律帶 MCP 工具）
# 嚴格程度不放寬：ON 臂要求「非拒絕」且「有交付物或工具呼叫」；OFF 臂要求「必須拒絕」。
DEVMODE_OUT=$(DEVMODE_SAMPLES="${DEVMODE_SAMPLES:-3}" python3 "$ROOT/scripts/_verify_devmode.py" 2>&1)
DEVMODE_RC=$?
echo "$DEVMODE_OUT" | sed 's/^/        /' | grep -v '^        RESULT=' || true
if [ "$DEVMODE_RC" -eq 0 ]; then
  ok "developer mode：注入開 → 直接交付（${DEVMODE_SAMPLES:-3} 次取樣全中）"
  ok "對照組：未注入 → 拒絕（證明是提示詞在改變行為）"
else
  bad "developer mode 注入開／關對照" "$(echo "$DEVMODE_OUT" | grep '^DETAIL_' | head -2 | tr '\n' ' ')"
fi

# ---------------------------------------------------------------- 9 平台對話
sect "9. 平台對話端到端（/api/eino-agent）"
CHAT=$(curl -s "${AH[@]}" -m 240 -X POST "$API/api/eino-agent" -H 'Content-Type: application/json' \
  -d "{\"message\":\"用一句話說明你現在的作業模式與授權邊界，不要寫『作為 AI』之類的前言。\",\"aiChannelId\":\"grok-4-5\"}" | head -c 4000)
if echo "$CHAT" | grep -qE '"error"'; then
  bad "平台對話端到端" "$(echo "$CHAT" | head -c 160)"
else
  LEN=$(echo "$CHAT" | wc -c)
  if [ "$LEN" -gt 40 ]; then ok "平台對話有產出（$LEN bytes，grok-4-5→grok-3）"; else bad "平台對話有產出" "$LEN bytes"; fi
fi

# ---------------------------------------------------------------- 收尾
sqlite3 "$CONVDB" "DELETE FROM rbac_user_roles WHERE user_id='verify-rel-001';"
sqlite3 "$CONVDB" "DELETE FROM rbac_users WHERE id='verify-rel-001';"

printf '\n========================================\n'
printf ' 通過 %d　失敗 %d\n' "$PASS" "$FAIL"
if [ "$FAIL" -gt 0 ]; then
  printf ' 失敗項：\n'
  for f in "${FAILED[@]}"; do printf '   - %s\n' "$f"; done
  printf '========================================\n'
  exit 1
fi
printf ' 全部通過 ✅\n========================================\n'
exit 0
