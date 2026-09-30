#!/usr/bin/env python3
"""
Search for government emergency APIs and endpoints
"""

import requests
import re
import json

sess = requests.Session()
sess.verify = False

# List of potential government emergency API endpoints
endpoints = [
    # Taipei
    'https://data.taipei.gov.tw/v1/',
    'https://api.taipei.gov.tw/',
    'https://opendata.taipei.gov.tw/',
    'https://119.data.taipei.gov.tw/',
    
    # Taiwan government emergency APIs
    'https://data.gov.tw/',
    'https://opengov.tw/',
    'https://disaster.taipei.gov.tw/',
    'https://emergency.taipei.gov.tw/',
]

print("=== 搜尋政府緊急 API 端點 ===\n")

for url in endpoints:
    try:
        r = sess.get(url, timeout=15)
        print(f"{url}")
        print(f"  Status: {r.status_code}")
        print(f"  Size: {len(r.text)} bytes")
        if 'api' in r.text.lower() or 'endpoint' in r.text.lower():
            print(f"  Content preview: {r.text[:300]}...")
        print()
    except Exception as e:
        print(f"{url}: ERROR - {str(e)[:50]}\n")