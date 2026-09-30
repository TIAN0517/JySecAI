#!/usr/bin/env python3
"""Phase 46: Download and analyze alerts.ncdr.nat.gov.tw JS files."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
BASE = 'https://alerts.ncdr.nat.gov.tw'

print("=== Downloading alerts.ncdr.nat.gov.tw JS files ===")

# Download main HTML
r = requests.get(BASE, proxies=PROXY, verify=False, timeout=20,
                headers={'User-Agent': 'Mozilla/5.0'})
html = r.text

# Find all JS files
js_files = re.findall(r'src=["\'](/web/static/js/[^"\']+)["\']', html)
print(f"JS files found: {js_files}")

for js in js_files:
    print(f"\nDownloading {js}...")
    r = requests.get(f'{BASE}{js}', proxies=PROXY, verify=False, timeout=30,
                    headers={'User-Agent': 'Mozilla/5.0'})
    print(f"  Status: {r.status_code}, Size: {len(r.text)}")
    
    if r.status_code == 200:
        content = r.text
        # Search for API key usage patterns
        print(f"  Searching for API key patterns...")
        
        # Look for Capapikey header usage
        capapikey_patterns = [
            r'Capapikey\s*[:=]\s*["\']([^"\']+)["\']',
            r'Capapikey\s*:\s*["\']([^"\']+)["\']',
            r'capapikey\s*=\s*["\']([^"\']+)["\']',
            r'headers\s*:\s*\{[^}]*Capapikey[^}]*\}',
        ]
        
        for pattern in capapikey_patterns:
            matches = re.findall(pattern, content, re.I)
            if matches:
                print(f"  Found Capapikey usage: {matches}")
                break
        
        # Search for AddValueApi endpoint calls
        api_calls = re.findall(r'AddValueApi[^"\']*["\']?', content)
        print(f"  AddValueApi references: {api_calls[:10]}")
        
        # Save the JS file
        safe_name = js.replace('/', '_').replace('.', '_')
        with open(f'/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_alerts_{safe_name}.js', 'w') as f:
            f.write(content)
        print(f"  Saved to: tpe119_evidence/ncdr_alerts_{safe_name}.js")

print("\nDone.")
