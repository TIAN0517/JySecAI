#!/usr/bin/env python3
"""Recon script for epcr.tpf.gov.tw"""
import urllib.request
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return f"HTTP {resp.status}\n{body[:3000]}"
    except Exception as e:
        return f"ERROR: {e}"

print("=== /config (port 4005) ===")
print(fetch("https://epcr.tpf.gov.tw:4005/config"))

print("\n=== Port 4004 root ===")
print(fetch("https://epcr.tpf.gov.tw:4004/"))

print("\n=== Port 4004 /config ===")
print(fetch("https://epcr.tpf.gov.tw:4004/config"))

print("\n=== Port 4004 /login (POST) ===")
data = json.dumps({"username":"admin","password":"admin","captcha":"1234"}).encode()
print(fetch("https://epcr.tpf.gov.tw:4004/login", method="POST", data=data,
            headers={"Content-Type":"application/json"}))

print("\n=== Port 4004 /captcha ===")
print(fetch("https://epcr.tpf.gov.tw:4004/captcha"))

print("\n=== Port 4000 root ===")
print(fetch("https://epcr.tpf.gov.tw:4000/"))

print("\n=== Port 4002 root ===")
print(fetch("https://epcr.tpf.gov.tw:4002/"))

print("\n=== Port 4005 /js/services.js ===")
print(fetch("https://epcr.tpf.gov.tw:4005/js/services.js"))

print("\n=== Port 4005 /js/controllers.js ===")
print(fetch("https://epcr.tpf.gov.tw:4005/js/controllers.js"))

print("\n=== Port 4005 /api ===")
print(fetch("https://epcr.tpf.gov.tw:4005/api"))

print("\n=== Port 4005 /api/users ===")
print(fetch("https://epcr.tpf.gov.tw:4005/api/users"))
