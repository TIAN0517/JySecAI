#!/usr/bin/env python3
"""Phase 49: Download and analyze the alerts.ncdr.nat.gov.tw app JS."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re, base64
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}

print("=== Downloading alerts.ncdr.nat.gov.tw JS ===")

# Get the homepage to find the actual JS file URLs
r = requests.get('https://alerts.ncdr.nat.gov.tw/', proxies=PROXY, verify=False, timeout=20,
                headers={'User-Agent': 'Mozilla/5.0'})
html = r.text

# Find all script src
scripts = re.findall(r'src=["\']([^"\']+)["\']', html)
print(f"Scripts: {scripts}")

# Also find inline scripts
inline_scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for i, s in enumerate(inline_scripts):
    if len(s.strip()) > 50:
        print(f"\nInline script {i}:")
        print(s[:500])
        # Search for API key
        api_key = re.findall(r'(?:Capapikey|api[_-]?key|apiKey)\s*[:=]\s*["\']([^"\']+)["\']', s, re.I)
        if api_key:
            print(f"  API key found: {api_key}")
        # Search for egovToken
        egov = re.findall(r'egovToken\s*[:=]\s*["\']([^"\']+)["\']', s, re.I)
        if egov:
            print(f"  egovToken found: {egov}")

# Download each JS file and save
for script in scripts:
    if script.endswith('.js'):
        url = script if script.startswith('http') else f'https://alerts.ncdr.nat.gov.tw{script}'
        try:
            r = requests.get(url, proxies=PROXY, verify=False, timeout=30,
                            headers={'User-Agent': 'Mozilla/5.0'})
            print(f"\nDownloading {script} -> {r.status_code}, len={len(r.text)}")
            
            if r.status_code == 200 and len(r.text) > 0:
                content = r.text
                
                # Search for API key patterns
                patterns = [
                    (r'Capapikey\s*[:=]\s*["\']([^"\']+)["\']', 'Capapikey'),
                    (r'api[_-]?key\s*[:=]\s*["\']([^"\']+)["\']', 'apiKey'),
                    (r'egovToken\s*[:=]\s*["\']([^"\']+)["\']', 'egovToken'),
                    (r'token\s*[:=]\s*["\']([A-Za-z0-9_\-]{10,})["\']', 'token'),
                ]
                
                for pattern, name in patterns:
                    matches = re.findall(pattern, content, re.I)
                    if matches:
                        print(f"  Found {name}: {matches}")
                
                # Search for AddValueApi endpoint
                api_refs = re.findall(r'AddValueApi[^"\']*', content)
                if api_refs:
                    print(f"  AddValueApi refs: {api_refs[:5]}")
                
                # Search for API endpoint calls
                api_calls = re.findall(r'(?:fetch|axios.get|axios.post)([^`]{0,200})(?:RealTime|EventCode|OrgCode|History)', content)
                if api_calls:
                    print(f"  API calls: {api_calls[:5]}")
                
                # Save the JS file
                filename = script.replace('/', '_').replace('.', '_')
                with open(f'/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_app_{filename}.js', 'w') as f:
                    f.write(content)
                print(f"  Saved: ncdr_app_{filename}.js")
        except Exception as e:
            print(f"  ERR: {str(e)[:60]}")

# Also check the alertsmodule.ncdr.nat.gov.tw (the embeddable component)
print("\n=== Checking alertsmodule.ncdr.nat.gov.tw ===")
r = requests.get('https://alertsmodule.ncdr.nat.gov.tw/', verify=False, timeout=20,
                headers={'User-Agent': 'Mozilla/5.0'})
html = r.text

# Find JS files
scripts2 = re.findall(r'src=["\'](/web/static/js/[^"\']+)["\']', html)
print(f"Scripts: {scripts2}")

# Search inline scripts
inline2 = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for i, s in enumerate(inline2):
    if len(s.strip()) > 50:
        # Search for API key
        api_key = re.findall(r'(?:Capapikey|api[_-]?key)\s*[:=]\s*["\']([^"\']+)["\']', s, re.I)
        if api_key:
            print(f"  API key in inline script {i}: {api_key}")
        egov = re.findall(r'egovToken\s*[:=]\s*["\']([^"\']+)["\']', s, re.I)
        if egov:
            print(f"  egovToken in inline script {i}: {egov}")

for script in scripts2:
    url = f'https://alertsmodule.ncdr.nat.gov.tw{script}'
    try:
        r = requests.get(url, verify=False, timeout=30,
                        headers={'User-Agent': 'Mozilla/5.0'})
        print(f"\nDownloading {script} -> {r.status_code}, len={len(r.text)}")
        
        if r.status_code == 200:
            content = r.text
            
            # Search for API key
            for pattern, name in [
                (r'Capapikey\s*[:=]\s*["\']([^"\']+)["\']', 'Capapikey'),
                (r'api[_-]?key\s*[:=]\s*["\']([^"\']+)["\']', 'apiKey'),
                (r'egovToken\s*[:=]\s*["\']([^"\']+)["\']', 'egovToken'),
            ]:
                matches = re.findall(pattern, content, re.I)
                if matches:
                    print(f"  Found {name}: {matches}")
            
            # Save
            filename = script.replace('/', '_').replace('.', '_')
            with open(f'/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_module_{filename}.js', 'w') as f:
                f.write(content[:50000])
            print(f"  Saved: ncdr_module_{filename}.js (first 50k)")
    except Exception as e:
        print(f"  ERR: {str(e)[:60]}")

print("\nDone.")
