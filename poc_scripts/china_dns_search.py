#!/usr/bin/env python3
"""
Search for DNS and endpoints for Taipei, Kaohsiung, Taoyuan cities
"""

import requests
import re
import json

def check_domain(domain):
    try:
        r = requests.get(f"https://{domain}", timeout=10, verify=False, allow_redirects=True)
        return {
            'domain': domain,
            'status': r.status_code,
            'final_url': r.url,
            'content_length': len(r.text),
            'title': re.search(r'<title>([^<]+)</title>', r.text)
        }
    except Exception as e:
        return {'domain': domain, 'error': str(e)}

# Taipei City domains
taipei_domains = [
    '119.gov.tw',
    'www.119.gov.tw',
    'ef.tpe.gov.tw',
    'emergency.tpe.gov.tw',
    'dispatch.119.gov.tw',
    'api.119.gov.tw',
    'www.dff.gov.tw',  # 臺北市消防局
    'fire.tpe.gov.tw',
    'emergency.tpe.gov.tw'
]

# Kaohsiung City domains
kaohsiung_domains = [
    'disaster.khh.gov.tw',
    'www.fire.khh.gov.tw',
    '119.khh.gov.tw',
    'dispatch.khh.gov.tw',
    'emergency.khh.gov.tw',
    'api.khh.gov.tw'
]

# Taoyuan City domains
taoyuan_domains = [
    'admin.ty.gov.tw',
    'www.fire.ty.gov.tw',
    '119.ty.gov.tw',
    'disaster.ty.gov.tw',
    'dispatch.ty.gov.tw',
    'emergency.ty.gov.tw'
]

results = {'taipei': [], 'kaohsiung': [], 'taoyuan': []}

print("=== 埋頭找 DNS 端點 ===\n")

print("--- 臺北市 ---")
for d in taipei_domains:
    r = check_domain(d)
    print(f"{r.get('domain', 'ERROR')}: {r.get('status', 'ERROR')} ({r.get('content_length', 0)} bytes)")

print("\n--- 高雄市 ---")
for d in kaohsiung_domains:
    r = check_domain(d)
    print(f"{r.get('domain', 'ERROR')}: {r.get('status', 'ERROR')} ({r.get('content_length', 0)} bytes)")

print("\n--- 桃園市 ---")
for d in taoyuan_domains:
    r = check_domain(d)
    print(f"{r.get('domain', 'ERROR')}: {r.get('status', 'ERROR')} ({r.get('content_length', 0)} bytes)")