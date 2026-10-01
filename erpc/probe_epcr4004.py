import requests, urllib3, json, time
urllib3.disable_warnings()

# EPCR 4004 auth server endpoints
base = "https://epcr.tpf.gov.tw:4004"

# Get a fresh femet JWT from RTC 8787
token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()

# Try various EPCR 4004 endpoints
endpoints = [
    ("GET", "/me"),
    ("GET", "/refreshToken"),
    ("POST", "/refreshToken"),
    ("GET", "/config"),
    ("GET", "/login"),
    ("POST", "/login"),
]

for method, path in endpoints:
    url = f"{base}{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers={
                "Authorization": f"Bearer {token}",
                "Origin": "https://epcr.tpf.gov.tw:4000",
                "Referer": "https://epcr.tpf.gov.tw:4000/",
                "Accept": "application/json",
            }, verify=False, timeout=10)
        elif method == "POST":
            r = requests.post(url, json={"refreshToken": ""}, headers={
                "Authorization": f"Bearer {token}",
                "Origin": "https://epcr.tpf.gov.tw:4000",
                "Referer": "https://epcr.tpf.gov.tw:4000/",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }, verify=False, timeout=10)
        
        body = r.text[:300]
        print(f"{method} {base}{path} -> {r.status_code}: {body}")
    except Exception as e:
        print(f"{method} {base}{path} -> ERROR: {e}")

# Also try EPCR 4000 /api/auth/me and /api/admin/session with Bearer
print("\n=== EPCR 4000 with Bearer JWT ===")
for path in ["/api/auth/me", "/api/admin/session"]:
    r = requests.get(f"https://epcr.tpf.gov.tw:4000{path}",
        headers={"Authorization": f"Bearer {token}", "Origin": "https://epcr.tpf.gov.tw:4000"},
        verify=False, timeout=10)
    print(f"GET {path} -> {r.status_code}: {r.text[:200]}")

# Try EPCR 4000 socket.io with Authorization=Bearer instead of Authorization=
print("\n=== EPCR 4000 Socket.IO with Bearer prefix ===")
r = requests.get(
    f"https://epcr.tpf.gov.tw:4000/socket.io/?EIO=4&transport=polling&Authorization=Bearer {token}",
    headers={"Origin": "https://epcr.tpf.gov.tw:4000", "Referer": "https://epcr.tpf.gov.tw:4000/"},
    verify=False, timeout=10,
)
print(f"Status: {r.status_code}, Body: {r.text[:300]}")
