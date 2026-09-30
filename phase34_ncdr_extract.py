#!/usr/bin/env python3
"""Phase 34: Extract all API endpoints from NCDR Swagger JSON."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, re, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}

# Get the swagger spec
r = requests.get('https://alerts.ncdr.nat.gov.tw/AddValueApi/swagger/v1/swagger.json', 
                 proxies=PROXY, verify=False, timeout=30,
                 headers={'Accept': 'application/json'})
spec = r.json()

print(f"=== Swagger Info ===")
info = spec.get('info', {})
print(f"Title: {info.get('title')}")
print(f"Version: {info.get('version')}")
print(f"Description: {info.get('description', '')[:200]}")

# Extract servers/basePath
servers = spec.get('servers', [])
base_path = spec.get('basePath', '')
print(f"\nServers: {servers}")
print(f"BasePath: {base_path}")
print(f"Host: {spec.get('host', '')}")

# Extract all paths
print(f"\n=== All API Paths ({len(spec.get('paths', {}))} paths) ===")
paths = spec.get('paths', {})
for path, methods in sorted(paths.items()):
    for method, info in methods.items():
        if isinstance(info, dict):
            summary = info.get('summary', '')
            description = info.get('description', '')
            tags = info.get('tags', [])
            print(f"\n  [{method.upper():6}] {path}")
            if tags:
                print(f"    Tags: {tags}")
            if summary:
                print(f"    Summary: {summary}")
            if description:
                print(f"    Desc: {description[:100]}")
            
            # Parameters
            params = info.get('parameters', [])
            for p in params:
                pname = p.get('name', '?')
                ptype = p.get('in', '?')
                req = p.get('required', False)
                ptype_val = p.get('type', p.get('schema', {}).get('type', ''))
                print(f"    Param: {pname} (in={ptype}, type={ptype_val}, required={req})")
            
            # Responses
            responses = info.get('responses', {})
            for code, resp in responses.items():
                print(f"    Response {code}: {str(resp.get('description',''))[:80]}")

# Extract all models/schemas
print(f"\n\n=== Models/Schemas ({len(spec.get('definitions', {}))} models) ===")
for name, schema in sorted(spec.get('definitions', {}).items()):
    props = schema.get('properties', {})
    print(f"\n  {name}:")
    for prop_name, prop_info in props.items():
        ptype = prop_info.get('type', prop_info.get('$ref', 'object').split('/')[-1])
        desc = prop_info.get('description', '')[:60]
        print(f"    {prop_name} ({ptype}) - {desc}")

# Save full spec
with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_swagger_full.json', 'w') as f:
    json.dump(spec, f, indent=2, ensure_ascii=False)
print(f"\nFull spec saved to ncdr_swagger_full.json")

# Also look for any "city" or "municipal" references
print(f"\n=== City/Municipal references in spec ===")
for path in sorted(paths.keys()):
    if any(kw in path.lower() for kw in ['city', 'municipal', 'county', 'region', 'area', 'town']):
        print(f"  {path}")
