#!/bin/bash
# 語法檢查 + wrapper 邏輯實測（不需要 root）
set -uo pipefail
BASE=/mnt/c/Users/Administrator/Desktop/JySecAI/taiwan-proxy
PASS=0; FAIL=0
ok()  { echo "  [ OK ] $*"; PASS=$((PASS+1)); }
bad() { echo "  [FAIL] $*"; FAIL=$((FAIL+1)); }

echo "=== 1. bash 語法檢查 ==="
for f in bin/scan-proxy-wrap install.sh verify.sh uninstall.sh; do
  if bash -n "$BASE/$f" 2>/tmp/synerr; then ok "$f 語法正確"
  else bad "$f 語法錯誤"; sed 's/^/           /' /tmp/synerr; fi
done

echo
echo "=== 2. wrapper 邏輯實測（模擬環境）==="
SB=/tmp/wraptest; rm -rf "$SB"; mkdir -p "$SB/bin"
cp "$BASE/bin/scan-proxy-wrap" "$SB/bin/scan-proxy-wrap"
chmod +x "$SB/bin/scan-proxy-wrap"

# 假工具：echo 出所有參數
mkdir -p "$SB/fakebin"
cat > "$SB/fakebin/probe" <<'EOF'
#!/bin/sh
printf '%s\n' "$@"
EOF
chmod +x "$SB/fakebin/probe"

# 模擬：把 REAL 指向假工具（用 bind 語意不必要，直接改一份副本）
sed "s#^REAL=\"/usr/bin/#REAL=\"$SB/fakebin/#" "$SB/bin/scan-proxy-wrap" > "$SB/bin/probe"
chmod +x "$SB/bin/probe"

printf '%-12s %s\n' probe -pTESTFLAG > "$SB/map.conf"

run() { JYSSECAI_SCAN_PROXY="$1" JYSSECAI_SCAN_PROXY_MAP="$SB/map.conf" "$SB/bin/probe" "${@:2}"; }

echo "--- B. 未設代理：零行為改變 ---"
out=$(env -u JYSSECAI_SCAN_PROXY JYSSECAI_SCAN_PROXY_MAP="$SB/map.conf" "$SB/bin/probe" -l http://x.invalid -silent)
exp=$'-l\nhttp://x.invalid\n-silent'
[ "$out" = "$exp" ] && ok "參數原樣傳遞" || { bad "參數被改動"; printf '%s\n' "$out" | sed 's/^/           /'; }

echo "--- C. 已設代理：正確注入 ---"
out=$(run 'socks5://203.0.113.9:1080' -l http://x.invalid -silent)
exp=$'-pTESTFLAG\nsocks5://203.0.113.9:1080\n-l\nhttp://x.invalid\n-silent'
[ "$out" = "$exp" ] && ok "注入在最前，其餘順序不變" || { bad "注入不符"; printf '%s\n' "$out" | sed 's/^/           /'; }

echo "--- D. 呼叫端自帶代理：不覆蓋 ---"
out=$(run 'socks5://203.0.113.9:1080' -p http://own:3128 -l http://x.invalid)
exp=$'-p\nhttp://own:3128\n-l\nhttp://x.invalid'
[ "$out" = "$exp" ] && ok "呼叫端優先，未覆蓋" || { bad "覆蓋了"; printf '%s\n' "$out" | sed 's/^/           /'; }

echo "--- D2. 呼叫端用 -x / -proxy 也應不覆蓋 ---"
out=$(run 'socks5://203.0.113.9:1080' -x http://own:3128)
exp=$'-x\nhttp://own:3128'
[ "$out" = "$exp" ] && ok "-x 未被覆蓋" || bad "-x 被覆蓋"
out=$(run 'socks5://203.0.113.9:1080' -proxy http://own:3128)
exp=$'-proxy\nhttp://own:3128'
[ "$out" = "$exp" ] && ok "-proxy 未被覆蓋" || bad "-proxy 被覆蓋"

echo "--- E. 未在對照表：完全不受影響 ---"
out=$(JYSSECAI_SCAN_PROXY='socks5://203.0.113.9:1080' JYSSECAI_SCAN_PROXY_MAP=/dev/null "$SB/bin/probe" -l http://x.invalid)
exp=$'-l\nhttp://x.invalid'
[ "$out" = "$exp" ] && ok "未啟用工具維持原生行為" || bad "未啟用工具被改動"

echo "--- F. 空參數 / 特殊值邊界 ---"
out=$(run 'socks5://203.0.113.9:1080')
exp=$'-pTESTFLAG\nsocks5://203.0.113.9:1080'
[ "$out" = "$exp" ] && ok "零額外參數時仍正確注入" || bad "零參數時異常"

out=$(run 'socks5://203.0.113.9:1080' 'target with spaces' 'ünïcödé')
exp=$'-pTESTFLAG\nsocks5://203.0.113.9:1080\ntarget with spaces\nünïcödé'
[ "$out" = "$exp" ] && ok "含空白/unicode 的參數安全透傳" || { bad "參數遭破壞"; printf '%s\n' "$out" | sed 's/^/           /'; }

echo "--- G. 對照表含註解行應可容忍 ---"
printf '# comment line\n\nprobe  -pTESTFLAG\n' > "$SB/map2.conf"
out=$(JYSSECAI_SCAN_PROXY='socks5://203.0.113.9:1080' JYSSECAI_SCAN_PROXY_MAP="$SB/map2.conf" "$SB/bin/probe" -l http://x.invalid)
exp=$'-pTESTFLAG\nsocks5://203.0.113.9:1080\n-l\nhttp://x.invalid'
[ "$out" = "$exp" ] && ok "註解與空行可正常跳過" || { bad "對照表解析異常"; printf '%s\n' "$out" | sed 's/^/           /'; }

echo "--- H. REAL 不存在時明確報錯 ---"
mkdir -p "$SB/empty"; cp "$SB/bin/scan-proxy-wrap" "$SB/empty/missingtool"; chmod +x "$SB/empty/missingtool"
out=$(JYSSECAI_SCAN_PROXY='socks5://x:1' JYSSECAI_SCAN_PROXY_MAP="$SB/map.conf" "$SB/empty/missingtool" 2>&1); rc=$?
[ "$rc" -eq 127 ] && echo "$out" | grep -q 'not found' && ok "缺原生執行檔時退出碼 127 且有訊息" || bad "缺原生執行檔時行為異常 (rc=$rc)"

rm -rf "$SB" /tmp/synerr
echo
echo "==============================================="
echo "  通過：$PASS    失敗：$FAIL"
echo "==============================================="
[ "$FAIL" -eq 0 ] || exit 1
