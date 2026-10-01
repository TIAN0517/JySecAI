#!/bin/bash
B="https://epcr.tpf.gov.tw:4004/login"
test_body() {
  local desc="$1"; local body="$2"
  # fresh session
  local cj=$(mktemp)
  curl -sk -c "$cj" --max-time 8 "https://epcr.tpf.gov.tw:4004/captcha" -o /dev/null
  local out=$(curl -sk -b "$cj" -H "Content-Type: application/json" --max-time 10 -d "$body" "$B" -w '|||%{http_code}')
  echo "[$desc] => ${out: -12}"
  rm -f "$cj"
}
test_body "empty obj" '{}'
test_body "no body" ''
test_body "user only" '{"username":"admin"}'
test_body "user+pass" '{"username":"admin","password":"admin"}'
test_body "full no-domain" '{"username":"admin","password":"admin","captcha":"1234"}'
test_body "user=nonexistent9x" '{"username":"zzz_nonexist_9x","password":"admin","captcha":"1234"}'
test_body "user+pass+cap+domain" '{"username":"admin","password":"admin","captcha":"1234","domain":"AUTH_SERVER"}'
test_body "GET-ish user root" '{"username":"root","password":"root","captcha":"1234"}'
