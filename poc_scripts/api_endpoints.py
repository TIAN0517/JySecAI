#!/usr/bin/env python3
"""
Test user management with proper CSRF handling for JSON
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
        
        # Try different endpoints
        print("=== Testing various admin AJAX endpoints ===")
        
        endpoints = [
            ("/admin/api/users", "list users"),
            ("/admin/api/settings", "list settings"),
            ("/admin/api/config", "list config"),
            ("/admin/api/logs", "list logs"),
            ("/admin/api/stats", "list stats"),
            ("/admin/api/reports", "list reports"),
            ("/admin/api/queries", "list queries"),
            ("/admin/api/searches", "list searches"),
            ("/admin/api/pagelogs", "list pagelogs"),
        ]
        
        for path, desc in endpoints:
            try:
                # GET
                r = sess.get(TARGET + path)
                print(f"GET {path}: {r.status_code} - {r.headers.get('Content-Type', 'None')}")
            except:
                pass