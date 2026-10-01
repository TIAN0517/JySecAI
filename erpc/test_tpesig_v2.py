import requests, urllib3, json, time, re, base64, hmac, hashlib
urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()

# Step 1: EIO=3 polling handshake with Host: tpesig.femet.com.tw
# The server offers websocket upgrade when Host is tpesig.femet.com.tw
r = requests.get(
    "https://tpertc.tfd.gov.tw:8787/socket.io/?EIO=3&transport=polling",
    headers={"Host": "tpesig.femet.com.tw"},
    verify=False, timeout=10
)
print(f"Handshake: {r.status_code} {r.text[:200]}")

# Step 2: Try EIO=4 with Host tpesig - it didn't offer websocket upgrades
r = requests.get(
    "https://tpertc.tfd.gov.tw:8787/socket.io/?EIO=4&transport=polling",
    headers={"Host": "tpesig.femet.com.tw"},
    verify=False, timeout=10
)
print(f"EIO=4 tpesig: {r.status_code} {r.text[:200]}")

# Step 3: Try EIO=3 with token in URL query
r = requests.get(
    f"https://tpertc.tfd.gov.tw:8787/socket.io/?EIO=3&transport=polling&token={token}",
    headers={"Host": "tpesig.femet.com.tw"},
    verify=False, timeout=10
)
print(f"EIO=3+token: {r.status_code} {r.text[:200]}")

# Step 4: Try EIO=4 with token in URL query
r = requests.get(
    f"https://tpertc.tfd.gov.tw:8787/socket.io/?EIO=4&transport=polling&token={token}",
    headers={"Host": "tpesig.femet.com.tw"},
    verify=False, timeout=10
)
print(f"EIO=4+token: {r.status_code} {r.text[:200]}")

# Step 5: Try EIO=3 with auth in the Socket.IO packet
# After getting SID, we need to send 0{auth} then try events
m = re.search(r'"sid":"([^"]+)"', r.text)
if m:
    sid = m.group(1)
    print(f"\nSID: {sid}")
    
    # Try EIO=3 websocket with proper headers
    # The issue is that websockets library sets its own Host header
    # Let's try with the correct Host
    
    # Actually, let me try EIO=4 with the tpesig Host - check if auth works differently
    sid4 = re.search(r'"sid":"([^"]+)"', r.text)
    if sid4:
        sid4 = sid4.group(1)
        # Send CONNECT with auth via polling
        body = f'0{{"token":"{token}"}}'
        r2 = requests.post(
            f"https://tpertc.tfd.gov.tw:8787/socket.io/?EIO=4&transport=polling&sid={sid4}",
            headers={"Host": "tpesig.femet.com.tw"},
            data=body,
            verify=False, timeout=10
        )
        print(f"POST auth: {r2.status_code} {r2.text[:200]}")
