#!/usr/bin/env python3
"""
Check server response headers
"""

import requests
import ssl

# Use the proper domain name
print("=== Server Headers Analysis ===")

# Create session that ignores cert
sess = requests.Session()
sess.verify = False
sess.headers.update({'Host': 'www.af-search.119.gov.taipei'})

try:
    r = sess.get("https://210.69.42.55/", timeout=10)
    print(f"Status: {r.status_code}")
    print(f"\nResponse Headers:")
    for k, v in r.headers.items():
        print(f"  {k}: {v}")
    
    # Check for interesting headers
    print(f"\n=== Security Analysis ===")
    
    # Check for security headers
    for h in ['X-Frame-Options', 'X-XSS-Protection', 'X-Content-Type-Options', 
              'Content-Security-Policy', 'Strict-Transport-Security']:
        if h in r.headers:
            print(f"  {h}: {r.headers[h]}")
        else:
            print(f"  {h}: NOT SET")
    
    # Check for server tech headers
    for h in ['Server', 'X-Powered-By', 'X-AspNet-Version']:
        if h in r.headers:
            val = r.headers[h]
            print(f"  [!] TECH LEAK] {h}: {val}")
except Exception as e:
    print(f"Error: {e}")

# Check specific endpoints with proper Host header
print(f"\n=== API Endpoints with Host Header ===")
admin_endpoints = [
    "/api/users",
    "/api/admin/users",
    "/api/v1/users",
    "/api/dispatch",
    "/api/triage",
    "/api/notify",
    "/api/push"
]

for endpoint in admin_endpoints:
    try:
        r = sess.get(f"https://210.69.42.55{endpoint}", timeout=5)
        print(f"  {endpoint}: {r.status_code} ({len(r.text)} bytes)")
    except Exception as e:
        print(f"  {endpoint}: ERROR")