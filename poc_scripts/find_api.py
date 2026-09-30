#!/usr/bin/env python3
"""
Search for actual API endpoints in JavaScript files
"""

import requests
import re

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

# Download main.js and look for API calls
r = sess.get(TARGET + "/js/main.js")
print(f"main.js size: {len(r.text)} bytes")

# Search for fetch() calls
fetch_calls = re.findall(r'fetch\([^)]*\)', r.text)
print(f"\nfetch() calls: {len(fetch_calls)}")
for call in fetch_calls:
    print(f"  {call[:100]}")

# Search for axios calls
axios_calls = re.findall(r'axios\.\w+\([^)]*\)', r.text)
print(f"\naxios calls: {len(axios_calls)}")

# Search for API URL patterns
api_urls = re.findall(r'["\'][^"\']*api[^"\']*["\']', r.text)
print(f"\nAPI URLs: {len(api_urls)}")
for url in api_urls:
    print(f"  {url}")