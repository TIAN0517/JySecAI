#!/usr/bin/env bash
# =============================================================================
# version.sh — 打印当前 payload 的版本信息，并可一键同步 runbook 里的 md5 / 版本码
#
#   用法:
#     bash scripts/version.sh              # 只打印（md5 / sha256 / ?v= 版本码 / 建议引入标签）
#     bash scripts/version.sh --patch      # 同时把 references/deploy-runbook.md
#                                         # 里的 md5 与 ?v= 版本码同步成当前值
#
#   为什么需要它: 改了 scripts/style.js 之后，线上引入标签的 ?v= 版本码必须跟着变，
#   否则浏览器会继续吃旧档（Last-Modified 启发式缓存可达数天）。
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

MD5="$(md5sum scripts/style.js | awk '{print $1}')"
SHA="$(sha256sum scripts/style.js | awk '{print $1}')"
VER="${MD5:0:8}"
RUNBOOK="references/deploy-runbook.md"

printf 'file     = scripts/style.js (%s bytes)\n' "$(wc -c < scripts/style.js | tr -d ' ')"
printf 'md5      = %s\n' "$MD5"
printf 'sha256   = %s\n' "$SHA"
printf 'version  = %s\n' "$VER"
printf '引入标签 = <script type="text/javascript" src="/style.js?v=%s"></script>\n' "$VER"

if [ "${1:-}" = "--patch" ]; then
  if [ ! -f "$RUNBOOK" ]; then
    echo "找不到 $RUNBOOK，跳过同步" >&2
    exit 2
  fi
  # 以 root 运行时 sed -i 会把文件属主改成 root，patch 后恢复原属主
  OWNER=""
  if [ "$(id -u)" = "0" ]; then
    OWNER="$(stat -c '%u:%g' "$RUNBOOK" 2>/dev/null || true)"
    echo "提示: 正在以 root 运行，patch 后会恢复原属主 ($OWNER)"
  fi
  # 1) Step 2 里“必须是”那一行的 32 位 md5（整行只有 md5）
  sed -i -E "s/^([0-9a-f]{32})$/$MD5/" "$RUNBOOK"
  # 2) 所有 ?v=xxxxxxxx 版本码
  sed -i -E "s|style\.js\?v=[0-9a-f]{8}|style.js?v=$VER|g" "$RUNBOOK"
  # 3) IOC 段里 v2（本技能包）`xxxx` 的 md5
  sed -i -E "s|(v2（本技能包）\`)[0-9a-f]{32}(\`)|\1$MD5\2|" "$RUNBOOK"
  [ -n "$OWNER" ] && chown "$OWNER" "$RUNBOOK" 2>/dev/null || true
  echo "已同步 $RUNBOOK 的 md5 与版本码 -> $VER"
  echo "剩余旧引用（应为空）:"
  grep -nE 'style\.js\?v=[0-9a-f]{8}|本技能包' "$RUNBOOK" | sed 's/^/  /'
fi
