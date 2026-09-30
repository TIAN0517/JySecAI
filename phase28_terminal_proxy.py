#!/usr/bin/env python3
"""Phase 28: EPCR backend probe via proxy using terminal Python."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept': '*/*'}

# Test both proxy endpoints
for proxy_hop, proxy_url in [('154:11085', 'socks5h://202.160.76.154:11085'), 
                              ('155:11084', 'socks5h://202.160.76.155:11084')]:
    try:
        proxies = {'https': proxy_url, 'http': proxy_url}
        r = requests.get('https://epcr.tpf.gov.tw:4002/', proxies=proxies, headers=HEADERS, verify=False, timeout=20)
        print(f"[{proxy_hop}] EPCR:4002/ -> {r.status_code}, len={len(r.text)}")
        title = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I)
        if title:
            print(f"  Title: {title.group(1).strip()}")
        # Find form
        forms = re.findall(r'<form[^>]*>(.*?)</form>', r.text, re.I | re.DOTALL)
        for f in forms[:2]:
            print(f"  Form: {f[:400]}")
        inputs = re.findall(r'name="([^"]+)"', r.text)
        if inputs:
            print(f"  Inputs: {inputs[:12]}")
        ct = r.headers.get('Content-Type', '')
        print(f"  CT: {ct}")
        
        # Get auth server
        r2 = requests.get('https://epcr.tpf.gov.tw:4004/', proxies=proxies, headers=HEADERS, verify=False, timeout=15)
        print(f"\n[{proxy_hop}] EPCR:4004/ -> {r2.status_code}, len={len(r2.text)}")
        ct2 = r2.headers.get('Content-Type', '')
        print(f"  CT: {ct2}")
        if r2.text and len(r2.text) < 500:
            print(f"  Body: {r2.text[:200]}")
        
        # Probe auth endpoints
        for path in ['/login', '/ssoLogin', '/sso/login', '/auth/login', '/captcha', '/users', '/health']:
            r3 = requests.get(f'https://epcr.tpf.gov.tw:4004{path}', proxies=proxies, headers=HEADERS, verify=False, timeout=10)
            ct3 = r3.headers.get('Content-Type', '')
            body3 = r3.text[:100] if r3.text else ''
            print(f"  :4004{path} -> {r3.status_code} [{ct3}] {body3}")
        break
    except Exception as e:
        print(f"[{proxy_hop}] Failed: {str(e)[:120]}")
