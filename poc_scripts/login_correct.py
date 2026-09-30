#!/usr/bin/env python3
"""
Correctly extract SVG captcha and login
"""

import requests
import re
import json

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

print("=== Login Process ===")

# Get login page
r = sess.get(f"{TARGET}/admin/login", timeout=10)
print(f"Step 1: Get login page: {r.status_code}")

# Extract CSRF token
token_match = re.search(r'name="_token" value="([^"]+)"', r.text)
if token_match:
    csrf_token = token_match.group(1)
    print(f"Step 2: CSRF Token: {csrf_token[:30]}...")
else:
    print("ERROR: No CSRF token found")
    exit(1)

# Get captcha SVG
r_captcha = sess.get(f"{TARGET}/admin/captcha", timeout=10)
print(f"Step 3: Get captcha: {r_captcha.status_code}")

# Extract text from SVG - look for the pattern used in this captcha
# Try multiple extraction methods
captcha_methods = []

# Method 1: Direct text elements
text_matches = re.findall(r'<text[^>]*>([A-Z0-9])</text>', r_captcha.text)
captcha_v1 = ''.join(text_matches)
print(f"  Method 1 (text elements): {captcha_v1}")

# Method 2: Text content between tags
svg_text = re.search(r'text>([A-Z0-9]+)', r_captcha.text)
if svg_text:
    captcha_v2 = svg_text.group(1)
    print(f"  Method 2 (svg text): {captcha_v2}")

# Method 3: Just use the pattern from earlier working code
captcha = captcha_v1 if captcha_v1 else 'AAAA'
print(f"Step 4: Using captcha: {captcha}")

# Login
login_data = {
    'username': 'admin',
    'password': 'admin',
    'captcha': captcha,
    '_token': csrf_token
}

print(f"Step 5: Submitting login...")
r_login = sess.post(f"{TARGET}/admin/login", data=login_data, allow_redirects=False, timeout=10)
print(f"  Login Status: {r_login.status_code}")

if r_login.status_code in [200, 302]:
    print(f"  Cookies: {list(sess.cookies.keys())}")
    
    # Test push endpoint
    print("\n=== Testing Push API ===")
    r_push = sess.post(f"{TARGET}/api/push", json={
        "message": "test notification",
        "to": "test@example.com"
    }, timeout=10)
    
    print(f"Status: {r_push.status_code}")
    print(f"Content-Type: {r_push.headers.get('Content-Type', 'N/A')}")
    
    try:
        data = r_push.json()
        print(f"JSON Response: {json.dumps(data, indent=2)[:500]}")
    except:
        text = r_push.text[:500]
        if text.strip():
            print(f"Text Response: {text}")