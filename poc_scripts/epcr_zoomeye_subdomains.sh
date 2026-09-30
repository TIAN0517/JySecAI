#!/bin/bash
# EPCR ZoomEye 子域名/資產監測腳本
# 更新日期: 2026-09-28
# 作者: Hermes Agent
#
# 此腳本使用 zoomeyeai CLI 搜尋台灣政府 EPCR (電子病歷) 系統
# 關鍵 dork: ssl.cert.subject.cn="epcr*" (唯一有效的搜尋方式)
#
# 使用前提:
# - zoomeyeai CLI 已安裝 (pip install zoomeyeai)
# - zoomeyeai init -apikey 0F4f3724-F434-7741-D7F9-A720f2316E7
# - 請勿透過 SOCKS proxy 執行 (會導致 TLS 錯誤)

set -e

ZOOMEYEAI="zoomeyeai"
EVIDENCE_DIR="tpe119_evidence/zoomeye_results"
mkdir -p "$EVIDENCE_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== EPCR ZoomEye 子域名監測 ==="
echo "執行時間: $(date)"
echo ""

# --- 關鍵搜尋 1: SSL 憑證主體 CN 搜尋 (最成功的 dork) ---
echo "--- 搜尋 1: ssl.cert.subject.cn=\"epcr*\" ---"
$ZOOMEYEAI search 'ssl.cert.subject.cn="epcr*"' -pagesize 50 -fields 'ip,port,domain,ssl' 2>&1 | \
  grep -v Warning | grep -v urllib3 > "$EVIDENCE_DIR/epcr_ssl_cert_${TIMESTAMP}.log"
grep -E "^(1[0-9]{1,}\.|61\.|163\.|35\.)" "$EVIDENCE_DIR/epcr_ssl_cert_${TIMESTAMP}.log" | head -20
echo "  完成: $EVIDENCE_DIR/epcr_ssl_cert_${TIMESTAMP}.log"
echo ""

# --- 搜尋 2: EPCR demo Cloudflare proxy 基礎設施 ---
echo "--- 搜尋 2: ip=\"35.234.50.28\" (Cloudflare proxy) ---"
$ZOOMEYEAI search 'ip="35.234.50.28"' -pagesize 100 -facets 'port' 2>&1 | \
  grep -v Warning | grep -v urllib3 > "$EVIDENCE_DIR/epcr_demo_ports_${TIMESTAMP}.log"
cat "$EVIDENCE_DIR/epcr_demo_ports_${TIMESTAMP}.log"
echo ""

# --- 搜尋 3: 台東縣完整子域 ---
echo "--- 搜尋 3: ssl.cert.subject.cn=\"*.ttfd.gov.tw\" ---"
$ZOOMEYEAI search 'ssl.cert.subject.cn="*.ttfd.gov.tw"' -pagesize 50 -fields 'ip,port,domain,ssl' 2>&1 | \
  grep -v Warning | grep -v urllib3 > "$EVIDENCE_DIR/epcr_ttwf_subdomains_${TIMESTAMP}.log"
grep -E "^(61\.222|210|59|125)" "$EVIDENCE_DIR/epcr_ttwf_subdomains_${TIMESTAMP}.log" | head -20
echo "  完成: $EVIDENCE_DIR/epcr_ttwf_subdomains_${TIMESTAMP}.log"
echo ""

# --- 搜尋 4: 台北市 EPCR ---
echo "--- 搜尋 4: ssl.cert.subject.cn=\"epcr*.gov.taipei\" ---"
$ZOOMEYEAI search 'ssl.cert.subject.cn="epcr*.gov.taipei"' -pagesize 50 -fields 'ip,port,domain,ssl' 2>&1 | \
  grep -v Warning | grep -v urllib3 > "$EVIDENCE_DIR/epcr_taipei_ssl_${TIMESTAMP}.log"
grep "TWCA" "$EVIDENCE_DIR/epcr_taipei_ssl_${TIMESTAMP}.log" | head -5
echo "  完成: $EVIDENCE_DIR/epcr_taipei_ssl_${TIMESTAMP}.log"
echo ""

# --- 失敗的 dork (記錄供學習) ---
echo "--- 失敗的 dork (不再使用) ---"
echo "  app=\"EPCR\" country=\"TW\" → 0 results (ZoomEye 不索引應用層標題)"
echo "  domain=\"tpf.gov.tw\" → 0 results (台北消防子域未被爬取)"
echo "  country=\"TW\" && port=4000 → 0 results (直接 port 搜尋無效)"
echo "  hostname=\"epcr.tpf.gov.tw\" → 0 results"
echo ""

echo "=== 監測完成 ==="
echo "所有結果存於: $EVIDENCE_DIR/"
echo "完整報告: data/poc_drafts/epcr_zoomeye_scan_report.md"
