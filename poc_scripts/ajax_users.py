#!/usr/bin/env python3
"""
Test POST AJAX endpoints for user management
"""

import requests
import json
import re

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False
sess.headers.update({'X-Requested-With': 'XMLHttpRequest'})

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
        
        # Test user management AJAX
        print("=== Testing POST /admin/users (user list) ===")
        r = sess.post(TARGET + "/admin/users", data={'action': 'list', '_token': token})
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('Content-Type', 'None')}")
        if r.text:
            print(f"Response: {r.text[:200]}")
        
        # Test user creation
        print("\n=== Testing POST /admin/users (create user) ===")
        r = sess.post(TARGET + "/admin/users", data={
            'action': 'create',
            'username': 'testuser',
            'password': 'test123',
            '_token': token
        })
        print(f"Status: {r.status_code}")
        if r.text:
            print(f"Response: {r.text[:200]}")