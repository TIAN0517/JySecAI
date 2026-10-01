import subprocess
import time
import os

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
ws_url = f"wss://tpertc.tfd.gov.tw:8787/socket.io/?EIO=3&transport=websocket&token={token}"

# Use wscat -n means no mask (server doesn't require it for EIO=3?)
# Actually we need proper websocket frames
# Let's use websocat if available, or build raw frames

# Check for websocat
r = subprocess.run(["which", "websocat"], capture_output=True, text=True)
print(f"websocat: {r.stdout.strip() or 'not found'}")

# Let's just try wscat with the tpesig Host by modifying /etc/hosts
print(f"\nToken: {token[:30]}...")

# Actually, let's try adding tpesig.femet.com.tw to /etc/hosts
# It might resolve to a different IP
print("\nChecking /etc/hosts...")
with open("/etc/hosts") as f:
    print(f.read())

# Let's try with curl websocket
# curl can do websocket upgrade
print("\nTrying curl websocket...")
r2 = subprocess.run([
    "curl", "-sS", "-m", "15", "-k",
    "-H", "Host: tpesig.femet.com.tw",
    "--include",
    "--upgrade", "websocket",
    ws_url
], capture_output=True, text=True, timeout=20)
print(f"curl stdout: {r2.stdout[:500]}")
print(f"curl stderr: {r2.stderr[:500]}")
