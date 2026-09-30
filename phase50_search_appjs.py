#!/usr/bin/env python3
"""Phase 50: Search app.js for API key and auth patterns."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import re

print("=== Searching app.js for API key and auth patterns ===")

with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_app__web_static_js_app_17b2ff38_js.js', 'r', errors='replace') as f:
    content = f.read()

print(f"File size: {len(content)} chars")

# Search for all Capapikey/AddValueApiKey patterns
patterns = [
    (r'AddValueApiKey[^"\']{0,30}', 'AddValueApiKey context'),
    (r'AddValueApiKey\s*[:=]\s*["\']([^"\']+)["\']', 'AddValueApiKey value'),
    (r'Capapikey\s*[:=]\s*["\']([^"\']+)["\']', 'Capapikey value'),
    (r'api[_-]?key\s*[:=]\s*["\']([A-Za-z0-9_\-]{4,})["\']', 'apiKey value'),
    (r'key[^a-zA-Z]["\'\s:=]([A-Za-z0-9_\-]{10,})["\']', 'key value'),
]

for pattern, name in patterns:
    matches = re.findall(pattern, content, re.I)
    if matches:
        print(f"\n{name} found ({len(matches)} matches):")
        for m in matches[:10]:
            print(f"  {m[:100]}")

# Search for the context around AddValueApiKey
addvalue_contexts = re.findall(r'(.{0,80}AddValueApiKey.{0,80})', content, re.I)
print(f"\n=== Context around AddValueApiKey ({len(addvalue_contexts)} matches) ===")
for ctx in addvalue_contexts[:5]:
    print(f"  ...{ctx}...")

# Search for header setup patterns
headers_patterns = [
    (r'headers\s*:\s*\{[^}]*Capapikey[^}]*\}', 'Capapikey in headers'),
    (r'setHeader[^;]*Capapikey', 'setHeader Capapikey'),
    (r'Capapikey.*[,}]', 'Capapikey context'),
]

for pattern, name in headers_patterns:
    matches = re.findall(pattern, content, re.I | re.DOTALL)
    if matches:
        print(f"\n{name} found:")
        for m in matches[:5]:
            print(f"  {m[:200]}")

# Search for the actual API endpoint calls
print("\n=== API endpoint references ===")
endpoints = re.findall(r'(RealTime|EventCode|OrgCode|History|apikey|AddValueApi/[^"\'\s,}]+)', content)
unique_endpoints = sorted(set(endpoints))
for ep in unique_endpoints:
    print(f"  {ep}")

# Search for any URL patterns
urls = re.findall(r'(https?://[^"\'\s<>{}`]+)', content)
print(f"\n=== URLs in app.js ({len(urls)} found) ===")
for url in sorted(set(urls))[:15]:
    print(f"  {url}")

# Search for geocode parameter usage
print("\n=== geocode usage ===")
geocode_ctxs = re.findall(r'.{0,50}geocode.{0,50}', content, re.I)
for ctx in geocode_ctxs[:5]:
    print(f"  {ctx}")

# Search for egovToken usage
print("\n=== egovToken usage ===")
egov_ctxs = re.findall(r'.{0,80}egovToken.{0,80}', content, re.I)
for ctx in egov_ctxs[:5]:
    print(f"  {ctx}")

# Search for any base64 encoded strings that might be the key
b64_pattern = re.findall(r'["\']([A-Za-z0-9+/]{20,}={0,2})["\']', content)
print(f"\n=== Base64-like strings ({len(b64_pattern)} found) ===")
for b in b64_pattern[:5]:
    try:
        import base64
        decoded = base64.b64decode(b).decode('utf-8', errors='ignore')
        if any(kw in decoded.lower() for kw in ['capapikey', 'apikey', 'ncdr', 'key', 'alert']):
            print(f"  {b[:40]} -> {decoded[:100]}")
    except:
        pass

# Search for hex encoded strings
hex_pattern = re.findall(r'["\']([0-9a-f]{16,})["\']', content, re.I)
print(f"\n=== Hex-like strings ({len(hex_pattern)} found) ===")
for h in hex_pattern[:5]:
    try:
        decoded = bytes.fromhex(h).decode('utf-8', errors='ignore')
        if any(kw in decoded.lower() for kw in ['capapikey', 'apikey', 'ncdr', 'key']):
            print(f"  {h} -> {decoded[:100]}")
    except:
        pass

print("\nDone.")
