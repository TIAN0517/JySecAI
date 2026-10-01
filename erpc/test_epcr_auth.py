import requests
import urllib3
import json
import time

urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()

# Step 1: Get EPCR config to see authServer
print("=== EPCR /config with no auth ===")
r = requests.get("https://epcr.tpf.gov.tw:4000/config", verify=False, timeout=15)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    cfg = r.json()
    print(json.dumps(cfg, indent=2)[:2000])
else:
    print(r.text[:200])

# Step 2: Get EPCR Socket.IO handshake (from hijack.py)
print("\n=== EPCR 4000 Socket.IO polling ===")
r = requests.get(
    "https://epcr.tpf.gov.tw:4000/socket.io/?EIO=4&transport=polling",
    verify=False, timeout=15,
)
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:500]}")

# Step 3: Try Socket.IO with Authorization query param
print("\n=== EPCR 4000 Socket.IO with Authorization ===")
r = requests.get(
    f"https://epcr.tpf.gov.tw:4000/socket.io/?EIO=4&transport=polling&Authorization=Bearer {token}",
    verify=False, timeout=15,
)
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:500]}")

# Step 4: Try the /rtc path on 4000 with connect.sid cookie
print("\n=== EPCR 4000 /rtc with PHP session cookie ===")
s = requests.Session()
# Login to RTC PHP to get session
s.post("https://tpertc.tfd.gov.tw/rtc/account.php?action=login",
    data={"acc": "femet", "pw": "femet123"}, allow_redirects=False, verify=False, timeout=10)
print(f"Cookies after login: {dict(s.cookies)}")

# Try accessing EPCR /rtc with the session
r = s.get("https://epcr.tpf.gov.tw:4000/rtc", verify=False, timeout=15, allow_redirects=False)
print(f"Status: {r.status_code}, Body: {r.text[:200]}")

# Step 5: Try EPCR 4000 /config with PHP session
print("\n=== EPCR 4000 /config with session cookie ===")
r = s.get("https://epcr.tpf.gov.tw:4000/config", verify=False, timeout=15)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    try:
        cfg = r.json()
        print(json.dumps(cfg, indent=2)[:500])
    except:
        print(r.text[:200])
else:
    print(r.text[:200])
