#!/usr/bin/env python3
"""
Explore admin endpoints after successful login
"""

import requests
import re
import json

TARGET = "https://210.69.42.55"
session = requests.Session()
session.verify = False

def get_captcha_chars():
    r = session.get(f"{TARGET}/admin/captcha")
    svg = r.text
    chars = re.findall(r'<text[^>]*>([A-Za-z0-9])</text>', svg)
    return ''.join(chars)

def do_login(username, password):
    r = session.get(f"{TARGET}/admin/login")
    token = re.search(r'name="_token" value="([^"]+)"', r.text)
    if not token:
        return None
    token = token.group(1)
    captcha = get_captcha_chars()
    
    data = {'_token': token, 'username': username, 'password': password, 'captcha': captcha}
    r = session.post(f"{TARGET}/admin/login", data=data, allow_redirects=False)
    return r.status_code == 302

# Login
if not do_login("admin", "admin"):
    print("[-] Login failed")
    exit(1)

print("[+] Logged in successfully\n")

# Test various admin paths
paths_to_test = [
    "/admin",
    "/admin/",
    "/admin/index",
    "/admin/home",
    "/admin/dashboard",
    "/admin/users",
    "/admin/config",
    "/admin/settings",
    "/admin/profile",
    "/admin/personnel",
    "/admin/finance",
    "/admin/data",
    "/admin/api",
    "/admin/search",
    "/admin/list",
    "/admin/report",
    "/admin/searchList",
    "/admin/listData",
]

print("=== Admin Path Testing ===")
for path in paths_to_test:
    r = session.get(f"{TARGET}{path}")
    print(f"{path}: {r.status_code} (len: {len(r.text)})")

# Check for possible API endpoints
print("\n=== Potential API Endpoints ===")
# Try common API patterns
api_patterns = [
    "/api",
    "/api/v1",
    "/api/v1/users",
    "/api/v1/config",
    "/api/v1/data",
    "/api/v1/search",
    "/api/admin",
    "/api/admin/users",
    "/api/admin/config",
]

for path in api_patterns:
    r = session.get(f"{TARGET}{path}")
    if r.status_code != 404 and "error" not in r.text.lower():
        print(f"{path}: {r.status_code} (possible API)")
        if r.headers.get('Content-Type', '').startswith('application/json'):
            print(f"  JSON: {r.text[:200]}...")

# Look for data in the main page
print("\n=== Data Discovery ===")
r = session.get(f"{TARGET}/")
# Look for AJAX endpoints or data URLs
ajax_patterns = re.findall(r'["\'](/[^"\']*\.(json|ajax|api)[^"\']*)["\']', r.text)
for m in ajax_patterns:
    print(f"Found potential API: {m[0]}")