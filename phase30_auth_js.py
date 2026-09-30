#!/usr/bin/env python3
"""Phase 30: Download EPCR auth server + hospital server JS files."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, re, json, os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PR = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
HE = {'User-Agent': 'Mozilla/5.0'}
save_dir = '/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/epcr_auth_server/'
os.makedirs(save_dir, exist_ok=True)

# Get full root pages
for name, url in [('auth_root', 'https://epcr.tpf.gov.tw:4004/'), 
                   ('hosp_root', 'https://epcr.tpf.gov.tw:4002/'),
                   ('epcr_root', 'https://epcr.tpf.gov.tw:4000/')]:
    try:
        r = requests.get(url, proxies=PR, headers=HE, verify=False, timeout=20)
        with open(f'{save_dir}{name}.html', 'w') as f:
            f.write(r.text)
        print(f"{name}: {r.status_code}, len={len(r.text)} -> saved")
        
        # Extract JS script src URLs
        js_urls = re.findall(r'src=["\']([^"\']+\.js)["\']', r.text)
        print(f"  JS refs: {len(js_urls)}")
        
        # Also find route config
        for js_url in js_urls[:5]:  # Just get the app-level ones
            if 'bower' in js_url:
                continue
            full_url = js_url if js_url.startswith('http') else url.replace('/', '//', 1)
            if js_url.startswith('/'):
                full_url = f"{url.rstrip('/')}{js_url}"
            elif not js_url.startswith('http'):
                full_url = f"{url.rstrip('/')}/{js_url}"
            
            try:
                r2 = requests.get(full_url, proxies=PR, headers=HE, verify=False, timeout=15)
                fname = js_url.replace('/', '_')
                with open(f'{save_dir}{name}_{fname}', 'w') as f:
                    f.write(r2.text)
                print(f"  {fname}: {r2.status_code}, len={len(r2.text)}")
            except Exception as e:
                print(f"  {js_url}: ERR {str(e)[:80]}")
    except Exception as e:
        print(f"{name}: ERR {str(e)[:100]}")

# Also try to POST to login endpoints
print("\n=== POST to auth endpoints ===")
for path in ['/sso/login', '/auth/login', '/api/login']:
    try:
        r = requests.post(f'https://epcr.tpf.gov.tw:4004{path}', proxies=PR, headers=HE, verify=False, timeout=15)
        print(f"  POST :4004{path} -> {r.status_code}, len={len(r.text)}")
        if len(r.text) < 500:
            print(f"  Body: {r.text[:200]}")
    except Exception as e:
        print(f"  POST :4004{path} -> ERR {str(e)[:80]}")

# Get the auth server's app.js or routes
print("\n=== Auth server routes ===")
for js_path in ['/app.js', '/scripts/app.js', '/js/app.js', '/config/routes.js', '/app/routes.js', '/Scripts/app.js']:
    try:
        r = requests.get(f'https://epcr.tpf.gov.tw:4004{js_path}', proxies=PR, headers=HE, verify=False, timeout=15)
        if r.status_code == 200 and len(r.text) > 100:
            fname = js_path.replace('/', '_')
            with open(f'{save_dir}auth_{fname}', 'w') as f:
                f.write(r.text)
            print(f"  GET :4004{js_path} -> {r.status_code}, len={len(r.text)} -> saved")
            # Find routes
            routes = re.findall(r"['\"](/[a-z][a-zA-Z0-9/_]+)['\"]", r.text)
            print(f"    Routes: {sorted(set(routes))[:20]}")
        else:
            print(f"  GET :4004{js_path} -> {r.status_code}, len={len(r.text)}")
    except Exception as e:
        print(f"  GET :4004{js_path} -> ERR {str(e)[:80]}")

print("\n=== Hospital server routes ===")
for js_path in ['/app.js', '/scripts/app.js', '/js/app.js', '/config/routes.js', '/app/routes.js', '/Scripts/app.js']:
    try:
        r = requests.get(f'https://epcr.tpf.gov.tw:4002{js_path}', proxies=PR, headers=HE, verify=False, timeout=15)
        if r.status_code == 200 and len(r.text) > 100:
            fname = js_path.replace('/', '_')
            with open(f'{save_dir}hosp_{fname}', 'w') as f:
                f.write(r.text)
            print(f"  GET :4002{js_path} -> {r.status_code}, len={len(r.text)} -> saved")
            routes = re.findall(r"['\"](/[a-z][a-zA-Z0-9/_]+)['\"]", r.text)
            print(f"    Routes: {sorted(set(routes))[:20]}")
        else:
            print(f"  GET :4002{js_path} -> {r.status_code}, len={len(r.text)}")
    except Exception as e:
        print(f"  GET :4002{js_path} -> ERR {str(e)[:80]}")
