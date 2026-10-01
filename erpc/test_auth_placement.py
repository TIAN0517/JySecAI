import requests, urllib3, json, re, base64, time
urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
host = "tpertc.tfd.gov.tw"
port = 8787

# The server sends 40 (CONNECT_ERROR) immediately after engine.io open
# This means auth is needed in the HTTP handshake, not in Socket.IO CONNECT
# Let's try different auth placements in the URL

# Test 1: token as direct query param (like the React app would via io())
print("=== Test: token in query (EIO=4) ===")
r = requests.get(
    f"https://{host}:{port}/socket.io/?EIO=4&transport=polling&token={token}",
    headers={"Host": "tpesig.femet.com.tw"},
    verify=False, timeout=10
)
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:300]}")
print(f"Set-Cookie: {r.headers.get('Set-Cookie', 'none')}")

# Test 2: JWT as Authorization header in polling
print("\n=== Test: Bearer in header (EUI=4) ===")
r2 = requests.get(
    f"https://{host}:{port}/socket.io/?EIO=4&transport=polling",
    headers={"Host": "tpesig.femat.com.tw", "Authorization": f"Bearer {token}"},
    verify=False, timeout=10
)
print(f"Status: {r2.status_code}")
print(f"Body: {r2.text[:300]}")

# Test 3: EUI=3 with token in query
print("\n=== Test: token in query (EUI=3) ===")
r3 = requests.get(
    f"https://{host}:{port}/socket.io/?EIO=3&transport=polling&token={token}",
    headers={"Host": "tpesig.femet.com.tw"},
    verify=False, timeout=10
)
print(f"Status: {r3.status_code}")
print(f"Body: {r3.text[:300]}")
print(f"Upgrades: {'websocket' in r3.text}")

# Test 4: No token, no Host change (baseline)
print("\n=== Test: no token, no tpesig Host (baseline) ===")
r4 = requests.get(
    f"https://{host}:{port}/socket.io/?EIO=4&transport=polling",
    verify=False, timeout=10
)
print(f"Status: {r4.status_code}")
print(f"Body: {r4.text[:200]}")
print(f"Upgrades: {'websocket' in r4.text}")

# Test 5: EUI=4 with tpesig Host, no token
print("\n=== Test: tpesig Host, no token (EUI=4) ===")
r5 = requests.get(
    f"https://{host}:{port}/socket.io/?EIO=4&transport=polling",
    headers={"Host": "tpesig.femet.com.tw"},
    verify=False, timeout=10
)
print(f"Status: {r5.status_code}")
print(f"Body: {r5.text[:300]}")

# Test 6: Try with JWT in cookie
print("\n=== Test: token in cookie ===")
r6 = requests.get(
    f"{host}:{port}/socket.io/?EIO=3&transport=polling",
    headers={"Host": "tpesig.femet.com.tw"},
    cookies={"cool-jwt": token, "io": "test"},
    verify=False, timeout=10
)
print(f"Status: {r6.status_code}")
print(f"Body: {r6.text[:300]}")
print(f"Upgrades: {'websocket' in r6.text}")
