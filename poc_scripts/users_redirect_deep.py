#!/usr/bin/env python3
"""
Deep dive into /api/users 302 redirect
"""

import requests
import re
import json

TARGET = "https://210.69.42.55"
session = requests.Session()
session.verify = False

# First login to get session
def login():
    r = session.get(TARGET + "/admin/login")
    token_match = re.search(r'name="_token" value="([^"]+)"', r.text)
    if not token_match:
        return False
    token = token_match.group(1)
    
    r = session.get(TARGET + "/admin/captcha")
    captcha_match = re.search(r'<text[^>]*>(\w)</text>', r.text)
    if not captcha_match:
        return False
    captcha = captcha_match.group(1)
    
    r = session.post(TARGET + "/admin/login", data={
        'username': 'admin',
        'password': 'admin',
        'captcha': captcha,
        '_token': token
    })
    return 'afsearch_session' in session.cookies

login()

print("=== Testing /api/users redirect ===")
r = session.get(TARGET + "/api/users")
print(f"Status: {r.status_code}")
if r.history:
    print(f"Redirected from: {r.history[-1].url} -> {r.url}")
    print(f"Redirect status: {r.history[-1].status_code}")

# Follow redirect manually
print("\n=== Manual redirect follow ===")
r = session.get(TARGET + "/api/users", allow_redirects=False)
print(f"Location: {r.headers.get('Location', 'None')}")
print(f"Content-Type: {r.headers.get('Content-Type', 'None')}")