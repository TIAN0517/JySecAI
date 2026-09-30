#!/bin/bash
# EPCR 系統驗證腳本
# 測試 Taipei (epcr.tpf.gov.tw) 和 Taitung (epcr.ttfd.gov.tw) EPCR 系統
# 注意: Taipei 系統位於防火牆後，無法直接存取

set -e

EVIDENCE_DIR="tpe119_evidence/zoomeye_results"
mkdir -p "$EVIDENCE_DIR"

echo "=== EPCR 系統驗證 ==="
echo "日期: $(date)"
echo ""

# 1. Taipei EPCR (epcr.tpf.gov.tw) - 預期失敗 (防火牆)
echo "--- 1. Taipei EPCR (epcr.tpf.gov.tw:4004) ---"
RESPONSE=$(curl -s --connect-timeout 10 -o /dev/null -w "%{http_code} %{time_total}" https://epcr.tpf.gov.tw:4004/ 2>&1 || echo "TIMEOUT")
echo "Status: $RESPONSE"
echo "(預期: 防火牆阻擋，連線逾時)"
echo ""

# 2. Taitung EPCR (epcr.ttfd.gov.tw:4004) - 可存取
echo "--- 2. Taitung EPCR (epcr.ttfd.gov.tw:4004) ---"
RESPONSE=$(curl -sk --connect-timeout 10 -o /dev/null -w "%{http_code} %{time_total}" https://61.222.211.111:4004/ 2>&1)
echo "Status: $RESPONSE"

# Test auth endpoint
echo "Auth /DispatchRecords (no token):"
curl -sk --connect-timeout 10 https://61.222.211.111:4004/DispatchRecords 2>&1 | tee "$EVIDENCE_DIR/epcr_taitung_auth_test.txt" | head -c 500
echo ""

# Test EPCR server
echo ""
echo "EPCR Server (port 4000):"
curl -sk --connect-timeout 10 https://61.222.211.111:4000/ 2>&1 | grep -oP '<title>[^<]+</title>' | head -1
echo ""

# Test MCI server
echo "MCI Server (port 4008):"
curl -sk --connect-timeout 10 https://61.222.211.111:4008/client/ 2>&1 | grep -oP '<title>[^<]+</title>' | head -1
echo ""

# 3. Taipei City EPCR (epcr.gov.taipei) - SSL cert found but server unreachable
echo "--- 3. Taipei City EPCR (epcr.gov.taipei:443) ---"
RESPONSE=$(curl -s --connect-timeout 10 -o /dev/null -w "%{http_code} %{time_total}" https://epcr.gov.taipei/ 2>&1 || echo "TIMEOUT")
echo "Status: $RESPONSE"
echo "(預期: 防火牆阻擋，連線逾時)"
echo ""

echo "=== 驗證完成 ==="
echo "Evidence saved to: $EVIDENCE_DIR/epcr_taitung_auth_test.txt"
