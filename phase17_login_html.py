#!/usr/bin/env python3
"""Phase 17: Get detailed HTML of the live login endpoints."""
import requests, urllib3, re, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

TARGETS = [
    ("af-search-admin-login", "https://210.69.42.55/admin/login"),
    ("af-search-admin", "https://210.69.42.55/admin"),
    ("fmet-login", "https://210.69.43.114/"),
    ("fmet-index", "https://210.69.43.114/index.php"),
]

for name, url in TARGETS:
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=10, allow_redirects=True)
        print(f"=== {name}: {url} ===")
        print(f"Status: {r.status_code}")
        print(f"Server: {r.headers.get('Server', 'N/A')}")
        print(f"Content-Type: {r.headers.get('Content-Type', 'N/A')}")
        print(f"Length: {len(r.text)} bytes")
        t = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I | re.S)
        print(f"Title: {t.group(1).strip() if t else 'N/A'}")
        # Extract forms
        forms = re.findall(r'<form[^>]*>.*?</form>', r.text, re.I | re.S)
        for i, form in enumerate(forms):
            print(f"\n  Form {i+1}: {form[:500]}")
        # Extract input fields
        inputs = re.findall(r'<input[^>]*>', r.text, re.I)
        for inp in inputs[:15]:
            print(f"  Input: {inp}")
        # Extract links
        links = re.findall(r'href=["\']([^"\']+)["\']', r.text)
        login_links = [l for l in links if any(w in l.lower() for w in ['login', 'admin', 'auth', 'api', 'register', 'forgot', 'reset'])]
        if login_links:
            print(f"\n  Login-related links: {login_links[:15]}")
        # Save
        with open(f"tpe119_evidence/login_pages/{name}.html", "w") as f:
            f.write(r.text[:10000])
        print(f"\n  Saved: tpe119_evidence/login_pages/{name}.html")
        print()
    except Exception as e:
        print(f"=== {name}: {url} === ERROR: {e}\n")
