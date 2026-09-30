#!/usr/bin/env python3
"""
Test long-polling endpoints for push functionality
"""

import requests
import json
import re
import time

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
        
        # Test each endpoint
        endpoints = ["/poll", "/longpoll", "/wait", "/api/poll", "/admin/poll"]
        
        for endpoint in endpoints:
            try:
                print(f"\n=== Testing {endpoint} ===")
                r = sess.get(TARGET + endpoint, timeout=10)
                print(f"Status: {r.status_code}")
                print(f"Content-Type: {r.headers.get('Content-Type', 'None')}")
                print(f"Size: {len(r.text)} bytes")
                
                # Check for JSON
                try:
                    data = json.loads(r.text)
                    print("JSON data:")
                    print(json.dumps(data, indent=2))
                except:
                    print("Not JSON")
                    # Show first 500 chars
                    print(r.text[:500])
            except requests.exceptions.Timeout:
                print(f"[TIMEOUT] {endpoint} (long polling)")
            except Exception as e:
                print(f"[ERROR] {endpoint}: {e}")