#!/usr/bin/env python3
"""
Access /admin/users with fresh session
"""

import requests
import re

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

# Login
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
        
        # Access users page
        print("=== Accessing /admin/users ===")
        r = sess.get(TARGET + "/admin/users")
        print(f"Status: {r.status_code}")
        
        if r.status_code == 302:
            print("Redirected (session expired)")
        else:
            print(f"Content-Type: {r.headers.get('Content-Type', 'None')}")
            print(f"Length: {len(r.text)} bytes")
            # Show content
            print("\n--- Content ---")
            print(r.text[:2000])