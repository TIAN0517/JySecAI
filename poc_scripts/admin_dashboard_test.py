#!/usr/bin/env python3
"""
Test admin-specific functionality
"""

import requests
import re
import json

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

# Login
print("=== Logging in ===")
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
        print(f"Session cookies: {list(sess.cookies.keys())}")
        
        # Try to access admin dashboard
        print("\n=== Testing admin dashboard ===")
        r = sess.get(TARGET + "/admin")
        print(f"Status: {r.status_code}")
        
        # Look for admin-specific content
        admin_indicators = [
            "Dashboard", "dashboard", "管理", "admin", "users",
            "Users", "logout", "Logout", "退出", "設定", "settings"
        ]
        
        for indicator in admin_indicators:
            if indicator in r.text:
                print(f"Found: {indicator}")