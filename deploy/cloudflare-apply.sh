#!/usr/bin/env bash
# JySecAI Cloudflare 一鍵套用腳本(DNS 檢查 + SSL 模式設定)
#
# 前置條件:
#   1. 權杖需移除 IP 限制(Cloudflare 後台 → 我的個人檔案 → API 權杖 → 編輯 → IP 篩選器)
#   2. 權杖權限需含:Zone.DNS(編輯)、Zone Settings(編輯)
# 用法:
#   CF_TOKEN=xxxx bash deploy/cloudflare-apply.sh
set -euo pipefail

CF_TOKEN="${CF_TOKEN:?請以 CF_TOKEN 環境變數傳入 API 權杖}"
ACCOUNT_ID="48f7a84a8cd2f94e4b583ae05e7e2d98"
ZONE_NAME="ccwu.cc"
EDGE_IP="52.128.238.210"   # 本機(Windows 邊緣)公網 IP
HOSTNAMES=(a b c bossai)   # 既有對外主機名(xss 走 /xss/ 路徑前綴,不需新 DNS)
API="https://api.cloudflare.com/client/v4"

call() {
  local method="$1" path="$2" data="${3:-}"
  if [[ -n "$data" ]]; then
    curl -s -X "$method" "$API$path" -H "Authorization: Bearer $CF_TOKEN" \
      -H "Content-Type: application/json" --data "$data"
  else
    curl -s -X "$method" "$API$path" -H "Authorization: Bearer $CF_TOKEN"
  fi
}

echo "── 1/4 驗證權杖 ──"
verify=$(call GET "/accounts/$ACCOUNT_ID/tokens/verify")
echo "$verify" | python -c "import json,sys;d=json.load(sys.stdin);assert d['success'],d;print('權杖有效:',d['result']['status'])"

echo "── 2/4 定位 zone: $ZONE_NAME ──"
zone_id=$(call GET "/zones?name=$ZONE_NAME" | python -c "import json,sys;d=json.load(sys.stdin);r=d.get('result') or [];assert r,'找不到 zone';print(r[0]['id'])")
echo "zone_id=$zone_id"

echo "── 3/4 檢查/補齊 DNS 記錄(Proxied) ──"
for h in "${HOSTNAMES[@]}"; do
  fqdn="$h.$ZONE_NAME"
  existing=$(call GET "/zones/$zone_id/dns_records?type=A&name=$fqdn")
  count=$(echo "$existing" | python -c "import json,sys;print(len(json.load(sys.stdin)['result'] or []))")
  if [[ "$count" -eq 0 ]]; then
    echo "  建立記錄 $fqdn → $EDGE_IP (proxied)"
    call POST "/zones/$zone_id/dns_records" \
      "{\"type\":\"A\",\"name\":\"$fqdn\",\"content\":\"$EDGE_IP\",\"proxied\":true,\"ttl\":1}" >/dev/null
  else
    echo "  已存在: $fqdn(跳過)"
  fi
done

echo "── 4/4 設定 SSL 模式: full(嚴格) ──"
call PATCH "/zones/$zone_id/settings/ssl" '{"value":"strict"}' \
  | python -c "import json,sys;d=json.load(sys.stdin);print('SSL 模式:',d['result']['value'] if d['success'] else d['errors'])"

echo ""
echo "完成。回呼對外網址格式:https://a.$ZONE_NAME/xss/api/xss/capture?token=<XSS_TOKEN>"
echo "提醒:edge 目前使用自簽憑證,Full(strict) 需換成 Cloudflare Origin 憑證;"
echo "      你貼的那張 Origin 憑證缺 SAN(只有 CN=Cloudflare),請在後台重產一張涵蓋 *.$ZONE_NAME 的。"
