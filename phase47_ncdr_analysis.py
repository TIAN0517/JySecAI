#!/usr/bin/env python3
"""Phase 47: Analyze how alerts.ncdr.nat.gov.tw website actually calls the API."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
BASE = 'https://alerts.ncdr.nat.gov.tw'

print("=== Analyzing website's API usage ===")

# 1. Download the main app JS file
r = requests.get(f'{BASE}/web/static/js/app.17b2ff38.js', proxies=PROXY, verify=False, timeout=30,
                headers={'User-Agent': 'Mozilla/5.0'})
app_js = r.text

# 2. Search for API call patterns
patterns = [
    # fetch() calls
    (r'fetch\(\s*["\']([^"\']+)["\']', 'fetch'),
    (r'fetch\(\s*`([^`]+)`', 'fetch template'),
    # axios calls
    (r'axios\.(get|post)\(\s*["\']([^"\']+)["\']', 'axios'),
    # XMLHttpRequest
    (r'open\(\s*["\'](\w+)["\']\s*,\s*["\']([^"\']+)["\']', 'XHR'),
    # API endpoint references
    (r'AddValueApi/([^"\']*)', 'API endpoint'),
    # API key references
    (r'(?:Capapikey|api[_-]?key|apiKey|token)\s*[:=]\s*["\']([^"\']+)["\']', 'API key'),
    # Header references
    (r'(?:headers|setHeader)\s*\([^)]*(?:Capapikey|Authorization)', 'Header setup'),
]

for pattern, name in patterns:
    matches = re.findall(pattern, app_js, re.I)
    if matches:
        print(f"\n{name.upper()} patterns found: {len(matches)}")
        for m in matches[:10]:
            if isinstance(m, tuple):
                print(f"  {m}")
            else:
                print(f"  {m[:100]}")

# 3. Search for specific API call sequences
api_call_patterns = [
    r'AddValueApi/[A-Za-z]+',
    r'/EventCode',
    r'/OrgCode',
    r'/RealTime',
    r'/History',
]

print("\n=== API call sequences in JS ===")
for pattern in api_call_patterns:
    matches = re.findall(pattern, app_js, re.I)
    if matches:
        print(f"{pattern}: {len(matches)} matches")

# 4. Check for any API key configuration
key_patterns = [
    r'(?:API_KEY|api_key|apiKey|APIKEY|Capapikey)\s*[:=]\s*["\']([^"\']+)["\']',
    r'(?:apiKey|api_key)\s*:\s*["\']([^"\']+)["\']',
]

print("\n=== API key configuration ===")
for pattern in key_patterns:
    matches = re.findall(pattern, app_js, re.I)
    if matches:
        print(f"Found: {matches}")

# 5. Look for any authentication or login flow
print("\n=== Auth/login flow ===")
auth_patterns = [
    r'(?:login|auth|token|session|cookie)',
    r'(?:Capapikey|CapApiKey|capapikey)',
]

for pattern in auth_patterns:
    matches = re.findall(pattern, app_js, re.I)
    if matches:
        print(f"{pattern}: {len(matches)} matches")

# 6. Check for any configuration object
config_patterns = [
    r'(?:config|Config|CONFIG|options|Options)\s*[:=]\s*\{[^}]*AddValueApi[^}]*\}',
    r'(?:baseUrl|apiUrl|apiBase)\s*[:=]\s*["\']([^"\']+)["\']',
]

print("\n=== Configuration objects ===")
for pattern in config_patterns:
    matches = re.findall(pattern, app_js, re.I)
    if matches:
        print(f"Found: {matches}")

# 7. Search for any API key in the HTML
r = requests.get(BASE, proxies=PROXY, verify=False, timeout=20,
                headers={'User-Agent': 'Mozilla/5.0'})
html = r.text

api_key_html = re.findall(r'(?:Capapikey|api[_-]?key|apiKey|token)["\s:=]+["\']?([A-Za-z0-9_\-]{8,})', html, re.I)
if api_key_html:
    print(f"\n=== API key in HTML ===")
    print(f"Found: {api_key_html}")

# 8. Check for environment variables or config files
env_files = ['.env', 'config.js', 'env.js', 'config.json', 'env.json']
for env_file in env_files:
    try:
        r = requests.get(f'{BASE}/{env_file}', proxies=PROXY, verify=False, timeout=10)
        if r.status_code == 200 and len(r.text) > 0:
            print(f"\n=== {env_file} ===")
            print(f"Content: {r.text[:500]}")
    except:
        pass

print("\nDone.")
