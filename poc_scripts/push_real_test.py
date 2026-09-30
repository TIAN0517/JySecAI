#!/usr/bin/env python3
"""
Test actual push functionality
"""

import requests
import re
import json

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

# Login
r = sess.get(f"{TARGET}/admin/login", timeout=10)
token = re.search(r'name="_token" value="([^"]+)"', r.text)
if not token:
    print("ERROR: No CSRF token")
    exit(1)
csrf_token = token.group(1)

r_captcha = sess.get(f"{TARGET}/admin/captcha", timeout=10)
captcha = ''.join(re.findall(r'<text[^>]*>([A-Z0-9])</text>', r_captcha.text))

r_login = sess.post(f"{TARGET}/admin/login", data={
    'username': 'admin',
    'password': 'admin',
    'captcha': captcha,
    '_token': csrf_token
}, allow_redirects=False, timeout=10)

print(f"Login: {r_login.status_code}")
print(f"Session: {dict(sess.cookies)}")

# Test push endpoint with actual data
print("\n=== Testing REAL Push Functionality ===")

push_payloads = [
    {
        'name': 'Telegram Push',
        'endpoint': '/api/telegram',
        'data': {
            '_token': csrf_token,
            'message': '測試推播訊息',
            'chat_id': '123456789'
        }
    },
    {
        'name': 'Web Push',
        'endpoint': '/api/push',
        'data': {
            '_token': csrf_token,
            'title': '消防警報',
            'body': '檢查站點',
            'url': 'https://example.com'
        }
    },
    {
        'name': 'Notification API',
        'endpoint': '/api/notify',
        'data': {
            '_token': csrf_token,
            'type': 'alert',
            'priority': 'high',
            'message': '測試通知'
        }
    }
]

for payload in push_payloads:
    r = sess.post(f"{TARGET}{payload['endpoint']}", 
                 data=json.dumps(payload['data']),
                 headers={'Content-Type': 'application/json'},
                 timeout=10)
    
    print(f"\n{payload['name']}:")
    print(f"  Status: {r.status_code}")
    try:
        resp = r.json()
        print(f"  Response: {json.dumps(resp, indent=2)[:400]}")
    except:
        print(f"  Text: {r.text[:300]}")