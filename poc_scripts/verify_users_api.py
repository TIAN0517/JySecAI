#!/usr/bin/env python3
"""
Verify /api/users behavior with fresh session
"""

import requests
import re

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

# Test WITHOUT login
print("=== Without login ===")
r = sess.get(TARGET + "/api/users", allow_redirects=False)
print(f"Status: {r.status_code}")
print(f"Location: {r.headers.get('Location', 'None')}")

# Login
print("\n=== With login ===")
r = sess.get(TARGET + "/admin/login")
token_match = re.search(r'name="_token" value="([^"]+)"', r.text)
if token_match:
    token = token_match.group(1)
    r = sess.get(TARGET + "/admin/captcha")
    captcha_match = re.search(r'<text[^>]*>(\w)</text>', r.text)
    if captcha_match:
        captcha = captcha_match.group(1)
        r = sess.post(TARGET + "/admin/login", data={
            'username': 'admin',
            'password': 'admin',
            'captcha': captcha,
            '_token': token
        })
        print(f"Login status: {r.status_code}")
        
        r = sess.get(TARGET + "/api/users", allow_redirects=False)
        print(f"Status: {r.status_code}")
        print(f"Location: {r.headers.get('Location', 'None')}")
        print(f"Content-Type: {r.headers.get('Content-Type', 'None')}")
        
        # Check if content differs
        if r.text != r.text:
            print("Content differs!")