#!/usr/bin/env python3
"""
Test push endpoints with authentication
"""

import requests
import json
import re

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False
sess.headers.update({'Host': 'www.af-search.119.gov.taipei'})

# Step 1: Get a valid session by logging in
print("=== Step 1: Login to get valid session ===")
r = sess.get(f"{TARGET}/admin/login", timeout=10)
token = re.search(r'name="_token" value="([^"]+)"', r.text)
if token:
    csrf_token = token.group(1)
    print(f"CSRF Token: {csrf_token[:20]}...")
    
    # Extract captcha
    r_captcha = sess.get(f"{TARGET}/admin/captcha", timeout=10)
    # SVG text extraction
    captcha_text = re.findall(r'<text[^>]*>([A-Z0-9])</text>', r_captcha.text)
    captcha = ''.join(captcha_text)
    print(f"Captcha: {''.join(captcha_text) if captcha_text else 'N/A'}")
    
    # Login
    login_data = {
        'username': 'admin',
        'password': 'admin',
        'captcha': ''.join(captcha_text) if captcha_text else 'AAAA',
        '_token': csrf_token
    }
    
    r_login = sess.post(f"{TARGET}/admin/login", data=login_data, timeout=10)
    print(f"Login Status: {r_login.status_code}")
    if r_login.status_code == 302:
        print(f"Redirected to: {r_login.headers.get('Location', 'N/A')}")