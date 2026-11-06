#!/usr/bin/env bash
# =============================================================================
# JySecAI scan-traffic proxy verifier
# -----------------------------------------------------------------------------
# 用法： sudo ./verify.sh
#
# 驗證四件事，全部不需要對任何真實目標發送請求：
#   A. wrapper 是否正確安裝
#   B. 「未設定代理」時是否為零行為改變（安全保證）
#   C. 「已設定代理」時是否正確注入參數
#   D. 呼叫端已自帶代理時是否不覆蓋
#   E. SOCKS5 出口是否在台灣
#   F. 服務的 PATH 順序是否讓 wrapper 真的會被採用
# =============================================================================
set -uo pipefail

WRAP=/usr/local/bin/scan-proxy-wrap
MAP=/etc/jysecai/scan-proxy-map.conf
TESTTOOL=jysec-proxy-test
PASS=0; FAIL=0
ok()   { echo "  [ OK ] $*"; PASS=$((PASS+1)); }
bad()  { echo "  [FAIL] $*"; FAIL=$((FAIL+1)); }
info() { echo "         $*"; }

[ "$(id -u)" -eq 0 ] || { echo "需要 root：請用 sudo" >&2; exit 1; }

# --- A. 安裝狀態 --------------------------------------------------------------
echo "=== A. 安裝狀態 ==="
[ -x "$WRAP" ] && ok "wrapper 已安裝：$WRAP" || { bad "wrapper 不存在：$WRAP"; echo "先執行 install.sh"; exit 1; }
[ -r "$MAP" ] && ok "對照表存在：$MAP" || bad "對照表不存在：$MAP"
echo "  --- 對照表內容 ---"; sed -n '1,20p' "$MAP" 2>/dev/null | sed 's/^/         /'
echo "  --- 符號連結 ---"
for l in /usr/local/bin/nuclei /usr/local/bin/ffuf; do
  [ -L "$l" ] && ok "$l -> $(readlink "$l")" || info "$l 非符號連結（可能未安裝）"
done

# --- 準備測試用假工具 --------------------------------------------------------
cat >"/usr/bin/$TESTTOOL" <<'EOF'
#!/bin/sh
printf '%s\n' "$@"
EOF
chmod 0755 "/usr/bin/$TESTTOOL"
cp "$WRAP" "/tmp/$TESTTOOL"
chmod 0755 "/tmp/$TESTTOOL"
printf '%-12s %s\n' "$TESTTOOL" "-pTESTPROXYFLAG" >/tmp/jysec-proxy-test-map.conf
trap 'rm -f "/usr/bin/$TESTTOOL" "/tmp/$TESTTOOL" /tmp/jysec-proxy-test-map.conf' EXIT

# --- B. 零行為改變保證 --------------------------------------------------------
echo
echo "=== B. 未設定代理時應為零行為改變 ==="
out=$(env -u JYSSECAI_SCAN_PROXY JYSSECAI_SCAN_PROXY_MAP=/tmp/jysec-proxy-test-map.conf \
      "/tmp/$TESTTOOL" -l http://example.invalid -silent 2>&1)
expect=$'-l\nhttp://example.invalid\n-silent'
if [ "$out" = "$expect" ]; then
  ok "參數原樣傳遞，未注入任何代理參數"
else
  bad "參數被改動"; info "got:"; printf '%s\n' "$out" | sed 's/^/           /'
fi

# --- C. 正確注入 --------------------------------------------------------------
echo
echo "=== C. 已設定代理時應正確注入 ==="
out=$(JYSSECAI_SCAN_PROXY='socks5://203.0.113.9:1080' \
      JYSSECAI_SCAN_PROXY_MAP=/tmp/jysec-proxy-test-map.conf \
      "/tmp/$TESTTOOL" -l http://example.invalid -silent 2>&1)
expect=$'-pTESTPROXYFLAG\nsocks5://203.0.113.9:1080\n-l\nhttp://example.invalid\n-silent'
if [ "$out" = "$expect" ]; then
  ok "代理參數已注入在最前面，其餘參數順序不變"
else
  bad "注入結果不符"; info "got:"; printf '%s\n' "$out" | sed 's/^/           /'
fi

# --- D. 不覆蓋呼叫端既有代理 --------------------------------------------------
echo
echo "=== D. 呼叫端已自帶代理時不應覆蓋 ==="
out=$(JYSSECAI_SCAN_PROXY='socks5://203.0.113.9:1080' \
      JYSSECAI_SCAN_PROXY_MAP=/tmp/jysec-proxy-test-map.conf \
      "/tmp/$TESTTOOL" -p http://caller.own.proxy:3128 -l http://example.invalid 2>&1)
expect=$'-p\nhttp://caller.own.proxy:3128\n-l\nhttp://example.invalid'
if [ "$out" = "$expect" ]; then
  ok "呼叫端自帶的代理優先，wrapper 未介入"
else
  bad "覆蓋了呼叫端的代理參數"; info "got:"; printf '%s\n' "$out" | sed 's/^/           /'
fi

# --- E. 不在對照表的工具不受影響 ---------------------------------------------
echo
echo "=== E. 未在對照表的工具應完全不受影響 ==="
out=$(JYSSECAI_SCAN_PROXY='socks5://203.0.113.9:1080' \
      JYSSECAI_SCAN_PROXY_MAP=/dev/null "/tmp/$TESTTOOL" -l http://example.invalid 2>&1)
expect=$'-l\nhttp://example.invalid'
if [ "$out" = "$expect" ]; then
  ok "未啟用的工具維持原生行為"
else
  bad "未啟用工具仍被改動"; info "got:"; printf '%s\n' "$out" | sed 's/^/           /'
fi

# --- F. PATH 順序 -------------------------------------------------------------
echo
echo "=== F. 服務 PATH 順序（決定 wrapper 是否會被採用）==="
for u in jysec-core jysec-kali-api jysec-hexstrike jysec-scanner-adapter; do
  p=$(systemctl show "$u" -p Environment --value 2>/dev/null | tr ' ' '\n' | grep '^PATH=' | head -1)
  if [ -z "$p" ]; then
    info "$u  未自訂 PATH（systemd 預設含 /usr/local/bin，順序正確）"
  else
    lu=$(echo "$p" | grep -bo '/usr/local/bin' | head -1 | cut -d: -f1)
    ub=$(echo "$p" | grep -bo '/usr/bin' | head -1 | cut -d: -f1)
    if [ -n "$lu" ] && [ -n "$ub" ] && [ "$lu" -lt "$ub" ]; then
      ok "$u  /usr/local/bin 在 /usr/bin 之前"
    else
      bad "$u  PATH 順序不利，wrapper 可能不會被採用：$p"
    fi
  fi
done

# --- G. 服務環境變數是否已注入 ------------------------------------------------
echo
echo "=== G. 服務環境變數 ==="
for u in jysec-core jysec-kali-api jysec-hexstrike jysec-scanner-adapter; do
  v=$(systemctl show "$u" -p Environment --value 2>/dev/null | tr ' ' '\n' | grep '^JYSSECAI_SCAN_PROXY=' | head -1)
  if [ -n "$v" ]; then ok "$u  $v"; else
    env_p=$(systemctl show "$u" -p EnvironmentFiles --value 2>/dev/null)
    if [ -n "$env_p" ]; then
      f=$(echo "$env_p" | awk '{print $1}' | head -1)
      if [ -r "$f" ] && grep -q '^JYSSECAI_SCAN_PROXY=' "$f" 2>/dev/null; then
        ok "$u  （由 $f 提供）"
      else
        bad "$u  尚未注入，且環境檔不可讀：$f"
      fi
    else
      bad "$u  尚未注入 JYSSECAI_SCAN_PROXY"
    fi
  fi
done

# --- H. SOCKS5 出口地理 -------------------------------------------------------
echo
echo "=== H. SOCKS5 出口地理 ==="
PROXYURL=$(grep -hoE 'JYSSECAI_SCAN_PROXY=socks5://[^ ]+' /etc/jysecai/scanner-adapter.env \
           /etc/systemd/system/jysec-core.service.d/10-scan-proxy.conf 2>/dev/null | head -1 | cut -d= -f2-)
if [ -z "$PROXYURL" ]; then
  info "未找到代理設定，略過"
else
  info "代理：$PROXYURL"
  hp=${PROXYURL#socks5://}
  geo=$(curl -s --max-time 20 --socks5-hostname "$hp" \
        'http://ip-api.com/json/?fields=status,country,countryCode,city,isp,as,proxy,hosting,query' 2>&1)
  echo "         $geo"
  if echo "$geo" | grep -q '"countryCode":"TW"'; then
    ok "出口在台灣"
  else
    bad "出口不在台灣"
  fi
fi

# --- 總結 --------------------------------------------------------------------
echo
echo "==============================================="
echo "  通過：$PASS    失敗：$FAIL"
echo "==============================================="
[ "$FAIL" -eq 0 ] || exit 1
