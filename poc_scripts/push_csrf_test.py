#!/usr/bin/env python3
"""
Test push API with CSRF header
"""

import requests
import re
import json

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

# Login
r = sess.get(f"{TARGET}/admin/login", timeout=10)
token = re.search(r'name="_token" value="([^"]+)"', r.text).group(1)
r_captcha = sess.get(f"{TARGET}/admin/captcha", timeout=10)
captcha = ''.join(re.findall(r'<text[^>]*>([A-Z0-9])</text>', r_captcha.text))

r_login = sess.post(f"{TARGET}/admin/login", data={
    'username': 'admin',
    'password': 'admin',
    'captcha': captcha,
    '_token': token
}, allow_redirects=False, timeout=10)

print(f"Login: {r_login.status_code}")
print(f"Cookies: {dict(sess.cookies)}")

# Get CSRF token from cookie or response
csrf_cookie = sess.cookies.get('XSRF-TOKEN', '')
print(f"CSRF Cookie: {csrf_cookie[:50]}...")

# Test various push endpoints with CSRF header
print("\n=== Testing Push Endpoints with CSRF Header ===")

push_endpoints = [
    '/api/push',
    '/api/notify',
    '/api/telegram',
    '/api/slack',
    '/webhook',
    '/callback'
]

for endpoint in push_endpoints:
    # Try with X-CSRF-TOKEN header
    sess.headers['X-CSRF-TOKEN'] = csrf_cookie
    
    r = sess.post(f"{TARGET}{endpoint}", json={
        "message": "test",
        "channel": "alerts",
        "priority": "high"
    }, timeout=10)
    
    print(f"\n{endpoint} (X-CSRF-TOKEN):")
    print(f"  Status: {r.status_code}")
    
    if r.status_code == 200:
        try:
            data = r.json()
            print(f"  Response: {json.dumps(data, indent=2)[:300]}")
        except:
            print(f"  Content: {r.text[:200]}")
    elif r.status_code == 419:
        # Try with raw body instead of JSON
        r2 = sess.post(f"{TARGET}{endpoint}", 
                      data=f"_token={token}&message=test",
                      headers={'Content-Type': 'application/x-www-form-urlencoded'},
                      timeout=10)
        print(f"  (form data) Status: {r2.status_code}")