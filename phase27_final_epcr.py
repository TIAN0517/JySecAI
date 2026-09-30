#!/usr/bin/env python3
"""Phase 27: Final EPCR backend probe via proxy."""
import requests, urllib3, re, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept': '*/*'}

# Proxy test
for proxy_url in ['socks5h://202.160.76.154:11085', 'socks5h://202.160.76.155:11084']:
    try:
        r = requests.get('https://epcr.tpf.gov.tw:4002/', proxies={'https': proxy_url, 'http': proxy_url}, headers=HEADERS, verify=False, timeout=30)
        print(f"[{proxy_url}] EPCR:4002/ -> {r.status_code}, len={len(r.text)}")
        title = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I)
        if title:
            print(f"  Title: {title.group(1).strip()}")
        # Find login form
        for m in re.finditer(r'<form[^>]*>(.*?)</form>', r.text, re.I | re.DOTALL):
            print(f"  Form action: {re.search(r'action=[\"']([^\"']+)[\"']', m.group(0))}")
            inputs = re.findall(r'name="([^"]+)"', m.group(0))
            print(f"  Input fields: {inputs}")
        break
    except Exception as e:
        print(f"[{proxy_url}] Failed: {str(e)[:100]}")

# Also try the auth server SSO login
for proxy_url in ['socks5h://202.160.76.154:11085', 'socks5h://202.160.76.155:11084']:
    try:
        r = requests.get('https://epcr.tpf.gov.tw:4004/sso/login', proxies={'https': proxy_url, 'http': proxy_url}, headers=HEADERS, verify=False, timeout=30)
        print(f"\n[{proxy_url}] EPCR:4004/sso/login -> {r.status_code}, len={len(r.text)}")
        title = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I)
        if title:
            print(f"  Title: {title.group(1).strip()}")
        for m in re.finditer(r'<form[^>]*>(.*?)</form>', r.text, re.I | re.DOTALL):
            print(f"  Form: {m.group(0)[:500]}")
        break
    except Exception as e:
        print(f"[{proxy_url}] EPCR:4004/sso/login Failed: {str(e)[:100]}")

# Try the auth server login page
for proxy_url in ['socks5h://202.160.76.154:11085', 'socks5h://202.160.76.155:11084']:
    try:
        r = requests.get('https://epcr.tpf.gov.tw:4004/', proxies={'https': proxy_url, 'http': proxy_url}, headers=HEADERS, verify=False, timeout=30)
        print(f"\n[{proxy_url}] EPCR:4004/ -> {r.status_code}, len={len(r.text)}")
        title = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I)
        if title:
            print(f"  Title: {title.group(1).strip()}")
        ct = r.headers.get('Content-Type', '')
        print(f"  CT: {ct}")
        if 'json' in ct:
            print(f"  JSON: {r.text[:500]}")
        elif len(r.text) < 2000:
            print(f"  Body: {r.text[:500]}")
        break
    except Exception as e:
        print(f"[{proxy_url}] EPCR:4004/ Failed: {str(e)[:100]}")
