#!/usr/bin/env python3
"""Phase 29: Extract EPCR auth server root page + try POST login."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, re, json, base64
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PR = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
HE = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}

# Get auth server root page
r = requests.get('https://epcr.tpf.gov.tw:4004/', proxies=PR, headers=HE, verify=False, timeout=20)
print(f"Auth root: {r.status_code}, len={len(r.text)}")
# Save full page
print(r.text[:2000])
print("\n---\n")

# Get Hospital Server page
r2 = requests.get('https://epcr.tpf.gov.tw:4002/', proxies=PR, headers=HE, verify=False, timeout=20)
print(f"Hosp root: {r2.status_code}, len={len(r2.text)}")
print(r2.text[:2000])
