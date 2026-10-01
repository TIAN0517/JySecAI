import requests, urllib3, json, re
urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
host = "tpertc.tfd.gov.tw"
port = 8787

# Step 1: GET polling handshake
r1 = requests.get(
    f"https://{host}:{port}/socket.io/?EIO=3&transport=polling",
    headers={"Host": "tpesig.femet.com.tw"},
    verify=False, timeout=10
)
print(f"GET: {r1.status_code} {r1.text}")

# The response contains: 96:0{sid}2:40
# 96:0{...} = engine.io OPEN
# 2:40 = engine.io MESSAGE with Socket.IO DISCONNECT

# But wait - in EUI=3, 40 might mean DISCONNECT (type 1), not CONNECT_ERROR
# In Socket.IO v2 (EUI=3): 0=connect, 1=disconnect, 2=event, 3=ack, 4=connect_error, 5=close

# Actually "2:40" might be engine.io message type 2 with payload "40"
# But engine.io message is type 4, not 2
# Let me re-parse: the format is <type><payload>
# "96:0{...}" means: length 96, type 0 (open), payload {...}
# "2:40" means: length 2, type 4 (message), payload "0"
# So "4" is engine.io MESSAGE and "0" is the Socket.IO CONNECT packet!

# Let me re-read: "96:0{\"sid\":\"...\"}" then "2:40"
# If it's "2:40", that's engine.io type 2 (ping)? No...
# Actually the format is: <engineio_type><length>:<payload>
# "96:0{...}" -> type 0 (open), length 96
# "2:40" -> type 2 (message), length... no

# Let me just parse it properly
body = r1.text
print(f"\nRaw body: {repr(body)}")

# In EUI=3 polling, the format is:
# <packet_type><body> for each engine.io packet, concatenated
# Or it could be: <length>:<packet_type><data>
# Let's check
for part in body.split(":"):
    print(f"  Part: {part[:100]}")
