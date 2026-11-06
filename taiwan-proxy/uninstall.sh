#!/usr/bin/env bash
# =============================================================================
# JySecAI scan-traffic proxy uninstaller
# -----------------------------------------------------------------------------
# 用法： sudo ./uninstall.sh            # 移除設定（保留日誌）
#        sudo ./uninstall.sh --purge    # 連日誌一起刪
#
# 完整回滾：不會殘留任何對掃描行為的影響，平台回到未安裝前狀態。
# =============================================================================
set -uo pipefail

PURGE=0
[ "${1:-}" = "--purge" ] && PURGE=1
[ "$(id -u)" -eq 0 ] || { echo "需要 root：請用 sudo" >&2; exit 1; }

echo "==> 移除符號連結"
for l in /usr/local/bin/nuclei /usr/local/bin/ffuf /usr/local/bin/subfinder /usr/local/bin/httpx; do
  if [ -L "$l" ] && [ "$(readlink "$l")" = "/usr/local/bin/scan-proxy-wrap" ]; then
    rm -f "$l"; echo "    已移除 $l"
  fi
done

echo "==> 移除 wrapper 本體"
rm -f /usr/local/bin/scan-proxy-wrap && echo "    已移除 /usr/local/bin/scan-proxy-wrap"

echo "==> 移除 systemd drop-in"
for u in jysec-core jysec-kali-api jysec-hexstrike jysec-scanner-adapter; do
  f="/etc/systemd/system/${u}.service.d/10-scan-proxy.conf"
  [ -f "$f" ] && rm -f "$f" && echo "    已移除 $f"
  rmdir "/etc/systemd/system/${u}.service.d" 2>/dev/null || true
done

echo "==> 移除 scanner-adapter.env 中的設定"
if [ -f /etc/jysecai/scanner-adapter.env ]; then
  sed -i '/^JYSSECAI_SCAN_PROXY=/d;/^JYSSECAI_SCAN_PROXY_MAP=/d;/^JYSSECAI_SCAN_PROXY_LOG=/d;/^JYSSECAI_SCAN_PROXY_DEBUG=/d' \
    /etc/jysecai/scanner-adapter.env
  echo "    已清除"
fi

echo "==> 移除對照表"
rm -f /etc/jysecai/scan-proxy-map.conf && echo "    已移除 /etc/jysecai/scan-proxy-map.conf"

if [ "$PURGE" -eq 1 ]; then
  rm -f /var/log/jysec-scan-proxy.log && echo "==> 已刪除日誌"
else
  echo "==> 保留日誌：/var/log/jysec-scan-proxy.log（--purge 可刪除）"
fi

systemctl daemon-reload
echo
cat <<'EOF'
==> 設定已移除。請重啟服務讓環境變數完全消失：

    sudo systemctl restart jysec-core jysec-kali-api jysec-hexstrike jysec-scanner-adapter

==> 確認沒有殘留：
    ls -la /usr/local/bin/nuclei 2>&1
    systemctl show jysec-core -p Environment --value | tr ' ' '\n' | grep JYSSECAI || echo "  無殘留"
EOF
