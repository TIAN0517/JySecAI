#!/usr/bin/env python3
"""
Comprehensive port and service enumeration for 210.69.42.55 and related domains
"""

import requests
import socket
import subprocess
import time

sess = requests.Session()
sess.verify = False

TARGET_IP = "210.69.42.55"

print("=" * 60)
print("Comprehensive Service Enumeration")
print("=" * 60)

# Check common ports
ports_to_check = [80, 443, 8080, 8443, 8888, 3000, 5000, 9000, 22, 3306, 5432]

print("\n=== Port Scanning ===")
for port in ports_to_check:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((TARGET_IP, port))
        if result == 0:
            print(f"Port {port}: OPEN")
        sock.close()
    except:
        pass

# Check for hidden admin interfaces
print("\n=== Hidden Admin Paths ===")
admin_paths = [
    "/manager/html",
    "/admin/login",
    "/wp-admin",
    "/phpmyadmin",
    "/.ssh",
    "/svn",
    "/.git",
    "/console",
    "/debug",
    "/_debug",
    "/upload",
    "/panel",
    "/backend",
    "/admin",
    "/ad",
    "/manage",
]

for path in admin_paths:
    try:
        r = sess.get(f"https://{TARGET_IP}{path}", timeout=3)
        if r.status_code != 404:
            print(f"{path}: {r.status_code}")
    except:
        pass

# Check for push notification endpoints
print("\n=== Push Notification Endpoints ===")
push_paths = [
    "/api/notify",
    "/api/push",
    "/api/telegram",
    "/api/slack",
    "/webhook",
    "/callback",
    "/notify",
    "/push",
    "/events",
    "/subscriptions",
]

for path in push_paths:
    try:
        # Try POST with JSON body
        r = sess.post(f"https://{TARGET_IP}{path}", 
                     json={"test": "data"}, timeout=3)
        if r.status_code not in [404]:
            print(f"{path}: {r.status_code} ({len(r.text)} bytes)")
            if r.headers.get('Content-Type', '').startswith('application/json'):
                print(f"  Response: {r.text[:200]}")
    except Exception as e:
        pass