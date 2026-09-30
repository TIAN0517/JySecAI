#!/usr/bin/env python3
"""FOFA search for Taiwan 119 dispatch systems via web scraping."""
import requests, json, urllib.parse

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}

# FOFA API v1 search endpoint
qbase64 = urllib.parse.quote("service119".encode().decode())
import base64
enc = base64.b64encode(b"service119.tfd.gov.tw").decode()

print("=== FOFA API v1 /search/all ===")
try:
    r = requests.get(
        f"https://api.fofa.info/v1/search/all?qbase64={enc}",
        headers=headers, timeout=15, verify=False
    )
    print(f"Status: {r.status_code}")
    print(r.text[:3000])
except Exception as e:
    print(f"Error: {e}")

print("\n=== FOFA host API ===")
try:
    r = requests.get(
        "https://api.fofa.info/v1/host/107.173.248.139",
        headers=headers, timeout=15, verify=False
    )
    print(f"Status: {r.status_code}")
    data = r.json()
    print(json.dumps(data, indent=2, ensure_ascii=False)[:3000])
except Exception as e:
    print(f"Error: {e}")

# Try FOFA web search page
print("\n=== FOFA web search page ===")
try:
    r = requests.get(
        "https://fofa.info/search?q=" + urllib.parse.quote("service119.tfd.gov.tw"),
        headers=headers, timeout=15, verify=False
    )
    print(f"Status: {r.status_code}")
    print(r.text[:2000])
except Exception as e:
    print(f"Error: {e}")
