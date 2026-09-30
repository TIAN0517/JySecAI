import sys, json, urllib.parse, requests
sys.path.insert(0, '.')
from broadcast_daemon import GROUP_ID, TELEGRAM_BOTS

city_code = "01"
token = TELEGRAM_BOTS[city_code]["token"]
msg = "🧪 test push from daemon"
payload = urllib.parse.urlencode({
    "chat_id": GROUP_ID, "text": msg, "parse_mode": "HTML"
}).encode()
print(f"payload type: {type(payload)}")
print(f"payload: {payload[:200]}")
print(f"payload decoded: {payload.decode()[:200]}")

# Try with dict data instead
resp = requests.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    timeout=10,
    data={"chat_id": GROUP_ID, "text": msg, "parse_mode": "HTML"}
)
print(f"dict-data Status: {resp.status_code}")
print(f"dict-data Body: {resp.text[:300]}")