import requests, urllib3, json, re, base64
urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
host = "tpertc.tfd.gov.tw"
port = 8787

# Step 1: GET polling handshake with tpesig Host
r1 = requests.get(
    f"https://{host}:{port}/socket.io/?EIO=3&transport=polling",
    headers={"Host": "tpesig.femet.com.tw"},
    verify=False, timeout=10
)

# Parse the body
body = r1.text
print(f"GET response body: {body[:200]}")

# Extract SID
sid_match = re.search(r'"sid":"([^"]+)"', body)
sid = sid_match.group(1) if sid_match else None
print(f"SID: {sid}")

# The body has two packets:
# 96:0{...} = engine.io OPEN
# 2:40 = engine.io MESSAGE with Socket.IO CONNECT_ERROR (40)

# Step 2: Send CONNECT with auth via POST
# In EUI=3, we send: 0{auth_json} as the message body
auth_data = f'0{{"token":"{token}"}}'
print(f"\nSending auth: {auth_data}")

r2 = requests.post(
    f"https://{host}:{port}/socket.io/?EIO=3&transport=polling&sid={sid}",
    headers={
        "Host": "tpesig.femet.com.tw",
    },
    cookies=r1.cookies,
    data=auth_data,
    verify=False, timeout=15
)
print(f"POST response: {r2.status_code}")
print(f"POST body: {r2.text[:300]}")

# Step 3: After auth, poll for messages
if r2.status_code == 200 and len(r2.text) > 0:
    print("\nPolling after auth...")
    for i in range(5):
        r3 = requests.get(
            f"https://{host}:{port}/socket.io/?EIO=3&transport=polling&sid={sid}",
            headers={"Host": "tpesig.femet.com.tw"},
            cookies=r1.cookies,
            verify=False, timeout=10
        )
        print(f"  Poll {i}: {r3.status_code} {r3.text[:200]}")
        if r3.status_code == 200 and r3.text:
            break
        time.sleep(1)

# Also try EUI=4 polling with auth POST
print("\n\n=== EUI=4 polling with auth ===")
r4 = requests.get(
    f"https://{host}:{port}/socket.io/?EIO=4&transport=polling",
    headers={"Host": "tpesig.femet.com.tw"},
    verify=False, timeout=10
)
sid4 = re.search(r'"sid":"([^"]+)"', r4.text).group(1) if '"sid":' in r4.text else None
print(f"EUI=4 SID: {sid4}")
print(f"EUI=4 body: {r4.text[:200]}")

# Send CONNECT auth
auth4 = f'0{{"token":"{token}"}}'
r5 = requests.post(
    f"https://{host}:{port}/socket.io/?EIO=4&transport=polling&sid={sid4}",
    headers={"Host": "tpesig.femet.com.tw"},
    cookies=r4.cookies,
    data=auth4,
    verify=False, timeout=15
)
print(f"Auth POST: {r5.status_code} {r5.text[:300]}")

# Check if we need to ack
if r5.text:
    # Send ACK back
    ack_data = f'3'  # ACK of the CONNECT
    r6 = requests.post(
        f"https://{host}:{port}/socket.io/?EIO=4&transport=polling&sid={sid4}",
        headers={"Host": "tpesig.femet.com.tw"},
        cookies=r4.cookies,
        data='3',
        verify=False, timeout=10
    )
    print(f"ACK: {r6.status_code} {r6.text[:200]}")
