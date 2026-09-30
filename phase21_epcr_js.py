#!/usr/bin/env python3
"""Phase 21: Extract EPCR SPA content + API endpoints from JS bundles."""
import requests, urllib3, re, json, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
PROXY = {"https": "socks5h://202.160.76.154:11085"}

s = requests.Session()
s.headers.update(HEADERS)
s.verify = False
s.proxies = PROXY

# Get EPCR pages and extract JS bundles + API endpoints
for port in [4000, 4002]:
    print(f"\n=== EPCR Port {port} Deep Analysis ===")
    url = f"https://118.163.107.93:{port}/"
    try:
        r = s.get(url, timeout=15)
        print(f"  Root page: {r.status_code}, len={len(r.text)}")
        
        # Extract JS bundles
        js_files = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', r.text)
        print(f"  JS bundles: {js_files[:10]}")
        
        # Save the full HTML
        with open(f"tpe119_evidence/login_pages/epcr_{port}_spa.html", "w") as f:
            f.write(r.text)
        
        # Extract API endpoint patterns from HTML/JS
        # Look for API patterns like /api/v1/..., /auth/..., fetch('/...'), etc.
        api_patterns = re.findall(r'["\'](/api/[^\s"\']+)["\']', r.text)
        auth_patterns = re.findall(r'["\'](/auth/[^\s"\']+)["\']', r.text)
        login_patterns = re.findall(r'["\']([/].*login[^\s"\']*)["\']', r.text, re.I)
        token_patterns = re.findall(r'["\']([/].*token[^\s"\']*)["\']', r.text, re.I)
        
        print(f"  API endpoints in HTML: {api_patterns[:15]}")
        print(f"  Auth endpoints: {auth_patterns[:10]}")
        print(f"  Login endpoints: {login_patterns[:10]}")
        print(f"  Token endpoints: {token_patterns[:10]}")
        
        # Download and analyze JS bundles
        for js_url in js_files[:5]:
            if js_url.startswith("http"):
                full_url = js_url
            elif js_url.startswith("/"):
                full_url = f"https://118.163.107.93:{port}{js_url}"
            else:
                full_url = f"https://118.163.107.93:{port}/{js_url}"
            try:
                rjs = s.get(full_url, timeout=10)
                print(f"\n  JS: {js_url} -> {rjs.status_code}, len={len(rjs.text)}")
                if rjs.status_code == 200:
                    # Save JS
                    safe_js = js_url.replace("/", "_").replace("?", "_").replace("&", "_")
                    with open(f"tpe119_evidence/login_pages/epcr_{port}_{safe_js}.js", "w") as f:
                        f.write(rjs.text[:50000])
                    # Extract API endpoints from JS
                    js_apis = re.findall(r'["\'](/[a-z]+/[a-z_]+)[^a-z][^\s"\'{}]+', rjs.text)
                    js_endpoint_apis = re.findall(r'["\'](/[a-z0-9_/.]+/(?:login|auth|token|api|v\d)/[^\s"\']*)["\']', rjs.text, re.I)
                    print(f"    API-like in JS: {js_endpoint_apis[:15]}")
                    # Extract all string literals that look like URLs
                    urls = re.findall(r'["\']((https?://[^\s"\']+|/[a-z][a-z0-9_/.-]+))["\']', rjs.text)
                    unique_urls = list(set(u[0] for u in urls))[:20]
                    print(f"    URLs/paths in JS: {unique_urls[:20]}")
            except Exception as e:
                print(f"  JS {js_url}: ERROR {str(e)[:80]}")
            time.sleep(0.3)
        
        # Also check the 401 response on /admin and /api
        for path in ["/admin", "/api", "/api/login", "/auth/login"]:
            r2 = s.get(f"https://118.163.107.93:{port}{path}", timeout=10)
            print(f"\n  :{port}{path}: {r2.status_code}")
            print(f"    WWW-Auth: {r2.headers.get('WWW-Authenticate', 'N/A')}")
            print(f"    Body: {r2.text[:300]}")
            time.sleep(0.2)
        
        new_session = False
        if not new_session:
            break  # Only port 4000 first
        
    except Exception as e:
        print(f"  ERROR: {str(e)[:200]}")
