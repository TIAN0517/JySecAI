#!/usr/bin/env python3
"""
Direct connection test bypassing SOCKS proxy
"""

import requests
import re

# Create session with no proxy
sess = requests.Session()
sess.verify = False
sess.trust_env = False  # Bypass system proxy settings

domains = [
    # Taipei City
    'www.tp.gov.tw',
    '119.taipei.gov.tw',
    'fire.tp.gov.tw',
    'disaster.tp.gov.tw',
    'dispatch.tp.gov.tw',
    'ef.tp.gov.tw',
    'epcr.taipei.gov.tw',
    '119.tp.gov.tw',
    
    # Kaohsiung City
    'www.khh.gov.tw',
    '119.khh.gov.tw',
    'fire.khh.gov.tw',
    'disaster.khh.gov.tw',
    'dispatch.khh.gov.tw',
    
    # Taoyuan City
    'www.ty.gov.tw',
    '119.ty.gov.tw',
    'fire.ty.gov.tw',
    'disaster.ty.gov.tw',
    'dispatch.ty.gov.tw',
    
    # New Taipei City
    'www.np.gov.tw',
    '119.np.gov.tw',
    'epcr.np.gov.tw',
    'fire.np.gov.tw',
    'disaster.np.gov.tw',
]

print("=== 直接連線測試 (Bypass SOCKS) ===\n")

for domain in domains:
    try:
        r = sess.get(f"https://{domain}", timeout=15)
        title = re.search(r'<title>([^<]+)</title>', r.text)
        title = title.group(1).strip()[:40] if title else "No title"
        print(f" ✓ https://{domain}")
        print(f"   {r.status_code} | {len(r.text)} bytes | {title}")
        if r.status_code == 200 and len(r.text) > 0:
            # Check for admin or API endpoints
            if 'admin' in r.text.lower():
                print(f"   [!] Contains 'admin' reference")
            if 'api' in r.text.lower():
                print(f"   [!] Contains 'api' reference")
    except Exception as e:
        print(f" ✗ https://{domain}")
        print(f"   {str(e)[:60]}")