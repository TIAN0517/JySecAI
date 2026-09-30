#!/usr/bin/env python3
"""
Check for internal services and different hosts
"""

import requests
import json

sess = requests.Session()
sess.verify = False

# Check if www.af-search.119.gov.taipei has different content
print("=== Comparing www.af-search.119.gov.taipei vs 210.69.42.55 ===")

try:
    # Use the proper domain
    sess.headers.update({'Host': 'www.af-search.119.gov.taipei'})
    r1 = sess.get("https://210.69.42.55/", timeout=10)
    print(f"www.af-search.119.gov.taipei: {len(r1.text)} bytes")
except Exception as e:
    print(f"Error: {e}")

# Try direct domain access (will fail but let's see what happens)
print("\n=== Checking potential internal IPs ===")

# Check if there are internal services based on headers
import subprocess
result = subprocess.run(['curl', '-k', '-s', '-I', 'https://210.69.42.55/'], 
                       capture_output=True, text=True, timeout=10)
print(result.stdout)