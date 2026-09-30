#!/usr/bin/env python3
"""
Check alternative endpoints and basic auth
"""

import requests

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

# Check with basic auth
print("=== HTTP Basic Auth: admin:admin ===")
r = sess.get(f"{TARGET}/admin/user", auth=('admin', 'admin'))
print(f"Status: {r.status_code}")
print(f"Content preview: {r.text[:500]}")

# Check mobile endpoint
print("\n=== /mobile ===")
r = sess.get(f"{TARGET}/mobile")
print(f"Status: {r.status_code}")
if "api" in r.text.lower() or "json" in r.text.lower():
    print("Content contains API/JSON references")
print(f"Content preview: {r.text[:500]}")

# Check v1 endpoint
print("\n=== /v1 ===")
r = sess.get(f"{TARGET}/v1")
print(f"Status: {r.status_code}")
print(f"Content preview: {r.text[:500]}")

# Check /app
print("\n=== /app ===")
r = sess.get(f"{TARGET}/app")
print(f"Status: {r.status_code}")
print(f"Content preview: {r.text[:500]}")