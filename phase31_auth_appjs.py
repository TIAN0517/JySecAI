#!/usr/bin/env python3
"""Phase 31: Download EPCR auth server app.js + find login form."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, re, os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PR = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
HE = {'User-Agent': 'Mozilla/5.0'}
save_dir = '/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/epcr_auth_server/'

# Get auth server login page - try multiple paths
for path in ['/js/app.js', '/js/login.js', '/js/LoginCtrl.js', '/login', '/js/controllers/login.js']:
    try:
        r = requests.get(f'https://epcr.tpf.gov.tw:4004{path}', proxies=PR, headers=HE, verify=False, timeout=15)
        print(f"  :4004{path} -> {r.status_code}, len={len(r.text)}, ct={r.headers.get('Content-Type','')}")
        
        if r.status_code == 200:
            fname = f'auth_{path.replace("/", "_")}'
            with open(f'{save_dir}{fname}', 'w') as f:
                f.write(r.text)
            
            if path.endswith('.js'):
                # Find routes and form references
                routes = re.findall(r"['\"](/[a-zA-Z0-9/_]+)['\"]", r.text)
                print(f"    Routes/paths: {sorted(set(routes))}")
                
                # Find login form structure
                forms = re.findall(r'<form[^>]*>(.*?)</form>', r.text, re.I | re.DOTALL)
                for f in forms:
                    print(f"    Form: {f[:300]}")
                
                # Find input field names
                inputs = re.findall(r'name=["\']([^"\']+)["\']', r.text)
                print(f"    Input names: {sorted(set(inputs))}")
                
                # Find template URLs
                templates = re.findall(r'templateUrl\s*:\s*["\']([^"\']+)["\']', r.text)
                print(f"    Templates: {templates}")
                
                # Find auth-related code
                auth_patterns = re.findall(r'[\'"](/auth/[a-z]+|post\\(["\']([a-z]+)["\']|login|logout|sso)[\'"]', r.text)
                if auth_patterns:
                    print(f"    Auth: {auth_patterns}")
            elif r.text:
                # HTML page - find login form
                title = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I)
                if title:
                    print(f"    Title: {title.group(1).strip()}")
                forms = re.findall(r'<form[^>]*action=["\']([^"\']+)["\'].*?>', r.text, re.I)
                print(f"    Form actions: {forms}")
                inputs = re.findall(r'name=["\']([^"\']+)["\']', r.text)
                print(f"    Inputs: {sorted(set(inputs))}")
    except Exception as e:
        print(f"  :4004{path} -> ERR {str(e)[:80]}")

# Also download the main JS bundle referenced in the root page
print("\n=== Auth server JS bundle extraction ===")
r = requests.get('https://epcr.tpf.gov.tw:4004/', proxies=PR, headers=HE, verify=False, timeout=15)
js_urls = re.findall(r'src=["\']([^"\']+\.js)["\']', r.text)
for js_url in js_urls:
    if 'bower' not in js_url and 'lib/' not in js_url:
        if not js_url.startswith('http'):
            if js_url.startswith('/'):
                full = f'https://epcr.tpf.gov.tw:4004{js_url}'
            else:
                full = f'https://epcr.tpf.gov.tw:4004/{js_url}'
        else:
            full = js_url
        try:
            r2 = requests.get(full, proxies=PR, headers=HE, verify=False, timeout=15)
            fname = js_url.replace('/js/', '').replace('/', '_')
            if r2.status_code == 200 and len(r2.text) > 50:
                with open(f'{save_dir}auth_bundle_{fname}', 'w') as f:
                    f.write(r2.text)
                routes = re.findall(r"['\"](/[a-zA-Z0-9/_]+)['\"]", r2.text)
                inputs = re.findall(r'name=["\']([^"\']+)["\']', r2.text)
                print(f"  {js_url}: {r2.status_code}, len={len(r2.text)} -> saved")
                print(f"    Routes: {sorted(set(routes))[:15]}")
                if inputs:
                    print(f"    Inputs: {sorted(set(inputs))[:15]}")
        except Exception as e:
            print(f"  {js_url}: ERR {str(e)[:80]}")
