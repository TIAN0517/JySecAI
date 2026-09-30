#!/usr/bin/env python3
"""
Check /admin/dashboard for actual content
"""

import requests
import re
from bs4 import BeautifulSoup

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
        
        # Check multiple admin pages
        for path in ["/admin/dashboard", "/admin/users", "/admin/settings", "/admin/config"]:
            print(f"\n=== {path} ===")
            r = sess.get(TARGET + path)
            print(f"Status: {r.status_code}, Size: {len(r.text)} bytes")
            
            # Check if different from main page
            main = sess.get(TARGET + "/")
            if r.text == main.text:
                print("Same as main page (default route)")
            else:
                print("DIFFERENT from main page!")
                # Show key content
                soup = BeautifulSoup(r.text, 'html.parser')
                title = soup.find('title')
                if title:
                    print(f"Title: {title.get_text()}")
                headings = soup.find_all(['h1', 'h2', 'h3'])
                for h in headings[:5]:
                    print(f"{h.name}: {h.get_text().strip()}")