#!/usr/bin/env python3
"""
Extract actual API data from /api/users
"""

import requests
import json
import re

sess = requests.Session()
sess.verify = False
sess.headers.update({'Host': 'www.af-search.119.gov.taipei'})

# Get fresh cookies with proper Host header
r = sess.get("https://210.69.42.55/", timeout=10)

# Now access the API endpoint
print("=== /api/users response ===")
r = sess.get("https://210.69.42.55/api/users", timeout=10)
print(f"Status: {r.status_code}")
print(f"Size: {len(r.text)} bytes")
print(f"Content-Type: {r.headers.get('Content-Type', 'unknown')}")

# Check if it's JSON
try:
    data = r.json()
    print("\n=== JSON DATA ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))
except:
    # Check for JSON-like content
    if '{"' in r.text or '[{' in r.text:
        print("\n=== Contains JSON-like content ===")
        print(r.text[:2000])
    else:
        # Check if it's HTML with data
        print("\n=== HTML Content (first 1500 chars) ===")
        print(r.text[:1500])