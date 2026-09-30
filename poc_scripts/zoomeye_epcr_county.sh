#!/usr/bin/env bash
# 正確語法的 ZoomEye 查詢批次（各縣市 119/EPCR 派遣系統登入口）
# 用法: bash poc_scripts/zoomeye_epcr_county.sh
set -u
cd /mnt/c/Users/Administrator/Desktop/JySecAI || exit 1
OUT=tpe119_evidence/zoomeye_results
mkdir -p "$OUT"
LOG="$OUT/epcr_county_$(date +%Y%m%d_%H%M).log"

filter() { grep -v -e RequestsDependencyWarning -e 'warnings.warn'; }

q() {
  local dork="$1"; shift
  echo "### $dork   [$*]"
  zoomeyeai search "$dork" "$@" 2>&1 | filter
  echo
}

{
  echo "== ZoomEye 各縣市 119/EPCR 查詢 @ $(date '+%F %T') =="
  echo

  echo "---- 1. 指紋類（EPCR 字樣）----"
  q 'title="epcr"'                      -pagesize 50
  q 'title="epcr" && country="TW"'      -pagesize 100
  q 'app="epcr"'                        -pagesize 50 -sub_type all
  q 'hostname="epcr*"'                  -pagesize 50 -sub_type all

  echo "---- 2. 各縣市消防/119 網域（web 子域）----"
  q 'domain="tfd.gov.tw"'               -pagesize 100 -sub_type web
  q 'domain="119.gov.taipei"'           -pagesize 100 -sub_type web
  q 'domain="tpf.gov.tw"'               -pagesize 100 -sub_type web
  q 'domain="ntpc.gov.tw"'              -pagesize 100 -sub_type web
  q 'domain="kcg.gov.tw"'               -pagesize 100 -sub_type web
  q 'domain="tycg.gov.tw"'              -pagesize 100 -sub_type web

  echo "---- 3. 標題關鍵字（派遣/救護/119）----"
  q 'country="TW" && title="派遣"'      -pagesize 100 -sub_type web
  q 'country="TW" && title="救護"'      -pagesize 100 -sub_type web
  q 'country="TW" && (title="119" || title="消防")' -pagesize 100 -sub_type web

  echo "---- 4. 已知 EPCR IP 反查 ----"
  q '(ip="118.163.107.93" || ip="202.160.76.185" || ip="35.234.50.28")' -pagesize 100 -sub_type all
} 2>&1 | tee "$LOG"

echo "[✔] 輸出: $LOG"
