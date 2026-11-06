#!/usr/bin/env bash
# =============================================================================
# JySecAI scan-traffic proxy installer
# -----------------------------------------------------------------------------
# 用法：
#   sudo ./install.sh                              # 安裝（不重啟服務）
#   sudo ./install.sh --proxy socks5://IP:PORT     # 指定代理
#   sudo ./install.sh --tools "nuclei ffuf subfinder"  # 指定要代理的工具
#   sudo ./install.sh --restart                    # 安裝後重啟服務
#
# 特性：冪等。重複執行不會產生重複項目。
# =============================================================================
set -euo pipefail

PROXY="${JYSSECAI_SCAN_PROXY:-socks5://202.160.76.165:11081}"
TOOLS="${JYSSECAI_SCAN_PROXY_TOOLS:-nuclei ffuf}"
DO_RESTART=0
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while [ $# -gt 0 ]; do
  case "$1" in
    --proxy)   PROXY="$2"; shift 2 ;;
    --tools)   TOOLS="$2"; shift 2 ;;
    --restart) DO_RESTART=1; shift ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

[ "$(id -u)" -eq 0 ] || { echo "需要 root：請用 sudo" >&2; exit 1; }

echo "==> 代理設定：$PROXY"
echo "==> 套用工具：$TOOLS"

# --- 1. 對照表：工具 -> 代理參數 ----------------------------------------------
MAP=/etc/jysecai/scan-proxy-map.conf
mkdir -p /etc/jysecai
: >"$MAP"
for t in $TOOLS; do
  case "$t" in
    nuclei|httpx|nmap)  f="-p"   ;;   # ProjectDiscovery 慣例
    ffuf)               f="-x"   ;;   # ffuf 慣例
    subfinder)          f="-proxy" ;; # subfinder 慣例
    katana)             f="-proxy" ;; # katana 慣例
    *)                  f="-p"   ;;
  esac
  # 只有原生執行檔真的存在才納入
  if [ -x "/usr/bin/$t" ]; then
    printf '%-10s %s\n' "$t" "$f" >>"$MAP"
  else
    echo "    略過 $t（/usr/bin/$t 不存在）"
  fi
done
chmod 0644 "$MAP"
echo "==> 對照表：$MAP"
sed -n '1,20p' "$MAP" | sed 's/^/    /'

# --- 2. 安裝 wrapper 本體 -----------------------------------------------------
install -m 0755 "$HERE/bin/scan-proxy-wrap" /usr/local/bin/scan-proxy-wrap
echo "==> 已安裝 /usr/local/bin/scan-proxy-wrap"

# --- 3. 為每個工具建立符號連結 -----------------------------------------------
for t in $TOOLS; do
  [ -x "/usr/bin/$t" ] || continue
  ln -sfn /usr/local/bin/scan-proxy-wrap "/usr/local/bin/$t"
  echo "==> 已連結 /usr/local/bin/$t -> scan-proxy-wrap"
done

# --- 4. 建立日誌檔 ------------------------------------------------------------
touch /var/log/jysec-scan-proxy.log
chmod 0640 /var/log/jysec-scan-proxy.log
chown root:jysec /var/log/jysec-scan-proxy.log 2>/dev/null || true
echo "==> 日誌：/var/log/jysec-scan-proxy.log"

# --- 5. 注入環境變數 ----------------------------------------------------------
if [ -f /etc/jysecai/scanner-adapter.env ]; then
  sed -i '/^JYSSECAI_SCAN_PROXY=/d;/^JYSSECAI_SCAN_PROXY_MAP=/d;/^JYSSECAI_SCAN_PROXY_LOG=/d;/^JYSSECAI_SCAN_PROXY_DEBUG=/d' \
    /etc/jysecai/scanner-adapter.env
  cat >>/etc/jysecai/scanner-adapter.env <<EOF
JYSSECAI_SCAN_PROXY=$PROXY
JYSSECAI_SCAN_PROXY_MAP=$MAP
JYSSECAI_SCAN_PROXY_LOG=/var/log/jysec-scan-proxy.log
EOF
  echo "==> 已更新 /etc/jysecai/scanner-adapter.env"
else
  echo "    略過 scanner-adapter.env（檔案不存在）"
fi

#    其餘服務用 systemd drop-in，不改動原 unit 檔
for u in jysec-core jysec-kali-api jysec-hexstrike jysec-scanner-adapter; do
  d="/etc/systemd/system/${u}.service.d"
  mkdir -p "$d"
  cat >"$d/10-scan-proxy.conf" <<EOF
# 由 JySecAI scan-traffic proxy 安裝產生
# 移除：sudo rm -f $d/10-scan-proxy.conf && sudo systemctl daemon-reload
[Service]
Environment=JYSSECAI_SCAN_PROXY=$PROXY
Environment=JYSSECAI_SCAN_PROXY_MAP=$MAP
Environment=JYSSECAI_SCAN_PROXY_LOG=/var/log/jysec-scan-proxy.log
EOF
  echo "==> 已建立 $d/10-scan-proxy.conf"
done

systemctl daemon-reload

# --- 6. 可選：重啟服務使環境變數生效 -------------------------------------------
if [ "$DO_RESTART" -eq 1 ]; then
  echo "==> 重新啟動服務..."
  systemctl restart jysec-core jysec-kali-api jysec-hexstrike jysec-scanner-adapter
  sleep 3
  for u in jysec-core jysec-kali-api jysec-hexstrike jysec-scanner-adapter; do
    printf '    %-26s %s\n' "$u" "$(systemctl is-active "$u" 2>&1)"
  done
else
  cat <<'EOF'

==> 環境變數需重啟服務才生效。確認無誤後執行：
      sudo systemctl restart jysec-core jysec-kali-api jysec-hexstrike jysec-scanner-adapter
    或直接重跑：sudo ./install.sh --restart
EOF
fi

echo
echo "==> 完成。驗證請執行：sudo ./verify.sh"
