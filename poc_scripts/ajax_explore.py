#!/usr/bin/env python3
"""
Test more AJAX endpoints with valid session
"""

import requests
import json
import re

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False
sess.headers.update({'X-Requested-With': 'XMLHttpRequest'})

# Login
def login():
    r = sess.get(TARGET + "/admin/login")
    token_match = re.search(r'name="_token" value="([^"]+)"', r.text)
    if not token_match:
        return False
    token = token_match.group(1)
    r = sess.get(TARGET + "/admin/captcha")
    captcha_match = re.search(r'<text[^>]*>(\w)</text>', r.text)
    if not captcha_match:
        return False
    captcha = captcha_match.group(1)
    r = sess.post(TARGET + "/admin/login", data={
        'username': 'admin',
        'password': 'admin',
        'captcha': captcha,
        '_token': token
    })
    return True

login()

# Test various AJAX endpoints
print("=== Testing AJAX endpoints ===")
endpoints = [
    "/admin/users",
    "/admin/settings",
    "/admin/config",
    "/admin/profile",
    "/admin/logs",
    "/admin/reports",
    "/admin/stats"
]

for ep in endpoints:
    print(f"\n--- {ep} (GET) ---")
    try:
        r = sess.get(TARGET + ep)
        print(f"Status: {r.status_code}")
        if r.headers.get('Content-Type', '').startswith('application/json'):
            print(f"JSON: {r.text[:200]}")
        else:
            print(f"Type: {r.headers.get('Content-Type', 'None')}")
            if len(r.text) < 100:
                print(f"Text: {r.text}")
    except Exception as e:
        print(f"Error: {e}")