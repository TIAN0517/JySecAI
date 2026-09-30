#!/usr/bin/env python3
"""
Test AJAX endpoints discovered in admin content
"""

import requests
import json

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False
sess.headers.update({'X-Requested-With': 'XMLHttpRequest'})

# Login first
r = sess.get(TARGET + "/admin/login")
import re
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
        
        # Test captcha refresh
        print("=== Testing /admin/captcha/refresh ===")
        r = sess.post(TARGET + "/admin/captcha/refresh", data={'_token': token})
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('Content-Type', 'None')}")
        if r.headers.get('Content-Type', '').startswith('application/json'):
            print(f"JSON: {r.text}")
        else:
            print(f"Text: {r.text[:200]}")