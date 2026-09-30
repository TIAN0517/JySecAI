#!/usr/bin/env python3
"""
Test push API endpoints with authenticated session
"""

import requests
import json

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False
sess.headers.update({
    'Host': 'www.af-search.119.gov.taipei',
    'Content-Type': 'application/json'
})

# Login first
import re
r = sess.get(f"{TARGET}/admin/login", timeout=10)
token = re.search(r'name="_token" value="([^"]+)"', r.text)
csrf_token = token.group(1) if token else ""

r_captcha = sess.get(f"{TARGET}/admin/captcha", timeout=10)
captcha_text = re.findall(r'<text[^>]*>([A-Z0-9])</text>', r_captcha.text)
captcha = ''.join(captcha_text) if captcha_text else 'AAAA'

login_data = {
    'username': 'admin',
    'password': 'admin',
    'captcha': captcha,
    '_token': csrf_token
}

r_login = sess.post(f"{TARGET}/admin/login", data=login_data, allow_redirects=False, timeout=10)
print(f"=== Login Response ===\nStatus: {r_login.status_code}")
print(f"Cookies: {dict(sess.cookies)}")

# Now test push endpoints
print("\n=== Testing Push Endpoints ===")
push_endpoints = ['/api/notify', '/api/push', '/api/telegram', '/api/slack']

for endpoint in push_endpoints:
    r = sess.post(f"{TARGET}{endpoint}", json={
        "message": "test",
        "channel": "general"
    }, timeout=10)
    
    print(f"\n{endpoint}:")
    print(f"  Status: {r.status_code}")
    print(f"  Content-Type: {r.headers.get('Content-Type', 'N/A')}")
    
    # Try to parse as JSON
    try:
        data = r.json()
        print(f"  JSON Response: {json.dumps(data, indent=2)[:500]}")
    except:
        # Show text response
        text = r.text[:500]
        if 'error' in text.lower() or 'message' in text.lower():
            print(f"  Text: {text}")