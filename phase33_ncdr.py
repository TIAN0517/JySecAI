#!/usr/bin/env python3
"""Phase 33: Explore NCDR alerts API - find all endpoints and municipal sub-endpoints."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, re, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
}

BASE = 'https://alerts.ncdr.nat.gov.tw'
SWAGGER_BASE = 'https://alerts.ncdr.nat.gov.tw/AddValueApi'

results = {}

# 1. Get swagger index
try:
    r = requests.get(f'{BASE}/AddValueApi/swagger/index.html', proxies=PROXY, headers=HEADERS, verify=False, timeout=30)
    print(f"[1] Swagger index: {r.status_code}, len={len(r.text)}")
    if r.status_code == 200:
        with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_swagger_index.html', 'w') as f:
            f.write(r.text)
        # Find swagger JSON/config URLs
        configs = re.findall(r'["\']?url["\']?\s*:\s*["\']([^"\']+)["\']', r.text)
        print(f"  Swagger config URLs: {configs}")
        # Look for swagger JSON file references
        json_refs = re.findall(r'["\']([^"\']*\.json)["\']', r.text)
        print(f"  JSON references: {json_refs}")
except Exception as e:
    print(f"[1] Error: {e}")

# 2. Common swagger config endpoints
for path in ['/swagger/config', '/swagger/config.json', '/swagger/v1/swagger.json', 
             '/swagger/v1/swagger.yaml', '/swagger/docs', '/swagger/docs/v1',
             '/swagger/v1/swagger.config', '/v1/swagger.json', '/v1/swagger.yaml',
             '/swagger', '/swagger/index.html']:
    try:
        r = requests.get(f'{BASE}{path}', proxies=PROXY, headers=HEADERS, verify=False, timeout=15)
        print(f"[2] GET {path} -> {r.status_code}, len={len(r.text)}, ct={r.headers.get('Content-Type','')[:50]}")
        if r.status_code == 200 and len(r.text) > 50:
            # Try to parse as JSON (swagger config often returns base64 encoded spec)
            try:
                data = r.json()
                if 'url' in data:
                    print(f"  -> Swagger config: url={data.get('url')}")
                if 'paths' in data:
                    print(f"  -> Direct swagger JSON with paths!")
                    for path_key in sorted(data.get('paths', {}).keys()):
                        methods = list(data['paths'][path_key].keys())
                        print(f"    {', '.join(methods).upper()} {path_key}")
            except:
                # Check if it's HTML with a spec URL
                spec_urls = re.findall(r'["\'](https?://[^"\']*swagger[^"\']*\.json[^"\']*)["\']', r.text)
                if spec_urls:
                    print(f"  -> Spec URLs: {spec_urls}")
    except Exception as e:
        print(f"[2] GET {path} -> ERR {str(e)[:80]}")

# 3. Try to get the actual swagger spec JSON
for spec_url in ['/swagger/v1/swagger.json', '/swagger/docs/v1', '/v1/swagger.json',
                 '/swagger/config', '/swagger/config.json']:
    try:
        r = requests.get(f'{BASE}{spec_url}', proxies=PROXY, headers={'Accept': 'application/json'}, verify=False, timeout=15)
        if r.status_code == 200:
            # Some Swagger configs return base64-encoded spec
            try:
                data = r.json()
                if isinstance(data, dict):
                    if 'spec' in data:
                        import base64
                        spec = base64.b64decode(data['spec']).decode('utf-8')
                        spec_data = json.loads(spec)
                    elif 'paths' in data:
                        spec_data = data
                    else:
                        continue
                    
                    print(f"\n=== API ENDPOINTS from {spec_url} ===")
                    paths = spec_data.get('paths', {})
                    for path, methods in sorted(paths.items()):
                        for method, info in methods.items():
                            print(f"  {method.upper():6} {path}")
                            if 'parameters' in info:
                                for p in info['parameters']:
                                    pname = p.get('name', '?')
                                    ptype = p.get('in', '?')
                                    print(f"         param: {pname} ({ptype})")
                            if 'responses' in info:
                                for code, resp in info['responses'].items():
                                    print(f"         resp {code}: {str(resp.get('description',''))[:60]}")
            except json.JSONDecodeError:
                pass
    except:
        pass

# 4. Try common AddValueApi paths
print("\n=== AddValueApi path probes ===")
for path in ['/AddValueApi/', '/AddValueApi/swagger', '/AddValueApi/api', 
             '/AddValueApi/v1', '/AddValueApi/config', '/AddValueApi/version',
             '/AddValueApi/health', '/AddValueApi/status', '/AddValueApi/openapi.json',
             '/AddValueApi/openapi', '/AddValueApi/swagger/v1/swagger.json']:
    try:
        r = requests.get(f'{BASE}{path}', proxies=PROXY, headers=HEADERS, verify=False, timeout=15)
        ct = r.headers.get('Content-Type', '')
        print(f"  GET {path} -> {r.status_code}, len={len(r.text)}, ct={ct[:50]}")
        if r.status_code == 200 and ('json' in ct.lower() or len(r.text) > 100):
            with open(f'/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_{path.strip("/").replace("/","_")}.json', 'w') as f:
                f.write(r.text[:5000])
    except Exception as e:
        print(f"  GET {path} -> ERR {str(e)[:60]}")

# 5. Try direct API patterns
print("\n=== Direct API probes ===")
for path in ['/AddValueApi/api/values', '/AddValueApi/api/alerts', '/AddValueApi/api/disaster',
             '/AddValueApi/api/city', '/AddValueApi/api/municipal', '/AddValueApi/api/county',
             '/AddValueApi/api/ncdr', '/AddValueApi/api/all', '/AddValueApi/api/list',
             '/AddValueApi/swagger/ui/index', '/AddValueApi/swagger/ui']:
    try:
        r = requests.get(f'{BASE}{path}', proxies=PROXY, headers=HEADERS, verify=False, timeout=15)
        print(f"  GET {path} -> {r.status_code}, len={len(r.text)}")
    except:
        pass

print("\nDone.")
