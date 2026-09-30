#!/usr/bin/env python3
"""
Test /showList with actual query data
"""

import requests
import json
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
        
        # Test showList
        print("=== POST /showList with test data ===")
        r = sess.post(TARGET + "/showList", data={
            'search': 'test',
            '_token': token
        })
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('Content-Type', 'None')}")
        if r.text:
            # Check for actual data
            if "test" in r.text.lower() or "result" in r.text.lower():
                print("Found query-related content!")
                print(r.text[:500])