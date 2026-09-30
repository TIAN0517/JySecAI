#!/usr/bin/env python3
"""Phase 20: Get EPCR page content + retry FSM with fresh session."""
import requests, urllib3, re, json, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
PROXY = {"https": "socks5h://202.160.76.154:11085"}

# === EPCR content extraction ===
print("=== EPCR System Content Extraction ===")
for port in [4000, 4001, 4002]:
    # Fresh session for each
    s = requests.Session()
    s.headers.update(HEADERS)
    s.verify = False
    s.proxies = PROXY
    
    url = f"https://118.163.107.93:{port}/"
    try:
        r = s.get(url, timeout=15, allow_redirects=True)
        print(f"\nPort {port}: {r.url} -> {r.status_code}, len={len(r.text)}")
        t = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I | re.S)
        print(f"  Title: {t.group(1).strip() if t else 'N/A'}")
        print(f"  Server: {r.headers.get('Server', 'N/A')}")
        print(f"  Content-Type: {r.headers.get('Content-Type', 'N/A')}")
        
        # Extract body preview
        # Remove scripts and styles for cleaner preview
        clean = re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=re.I | re.S)
        clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.I | re.S)
        clean = re.sub(r'<[^>]+>', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        print(f"  Text preview: {clean[:500]}")
        
        # Find forms
        forms = re.findall(r'<form[^>]*>(.*?)</form>', r.text, re.I | re.S)
        for i, form in enumerate(forms):
            action = re.search(r'action=["\']([^"\']*)["\']', form, re.I)
            method = re.search(r'method=["\']([^"\']*)["\']', form, re.I)
            inputs = re.findall(r'<input[^>]*>', form, re.I)
            print(f"\n  Form {i+1}: action={action.group(1) if action else 'N/A'}, method={method.group(1) if method else 'GET'}")
            for inp in inputs[:8]:
                name = re.search(r'name=["\']([^"\']*)["\']', inp)
                typ = re.search(r'type=["\']([^"\']*)["\']', inp)
                print(f"    Input: name={name.group(1) if name else '?'}, type={typ.group(1) if typ else 'text'}")
        
        # Save full page
        with open(f"tpe119_evidence/login_pages/epcr_port{port}_full.html", "w") as f:
            f.write(r.text[:15000])
        
        # Also probe login paths
        for path in ["/login", "/admin", "/api/login", "/auth/login", "/api", "/"]:
            if path == "/":
                continue
            try:
                r2 = s.get(f"https://118.163.107.93:{port}{path}", timeout=10, allow_redirects=True)
                print(f"  :{port}{path}: {r2.status_code}, len={len(r2.text)}")
            except:
                print(f"  :{port}{path}: ERROR")
    except Exception as e:
        print(f"\nPort {port}: ERROR {str(e)[:150]}")

print("\n\n=== FSM Fresh Session Probe ===")
# Fresh session for FSM
s2 = requests.Session()
s2.headers.update(HEADERS)
s2.verify = False
s2.proxies = PROXY
try:
    r = s2.get("https://fsm.119.gov.taipei/w/fsm119/index", timeout=15, allow_redirects=True)
    print(f"FSM /w/fsm119/index: {r.status_code}, len={len(r.text)}")
    print(f"  Final URL: {r.url}")
    t = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I | re.S)
    print(f"  Title: {t.group(1).strip() if t else 'N/A'}")
    # Save
    with open("tpe119_evidence/login_pages/fsm_index.html", "w") as f:
        f.write(r.text[:15000])
    
    # Check for login forms
    forms = re.findall(r'<form[^>]*>(.*?)</form>', r.text, re.I | re.S)
    for i, form in enumerate(forms):
        action = re.search(r'action=["\']([^"\']*)["\']', form, re.I)
        inputs = re.findall(r'<input[^>]*>', form, re.I)
        print(f"  Form {i+1}: action={action.group(1) if action else 'N/A'}")
        for inp in inputs[:8]:
            name = re.search(r'name=["\']([^"\']*)["\']', inp)
            typ = re.search(r'type=["\']([^"\']*)["\']', inp)
            print(f"    Input: name={name.group(1) if name else '?'}, type={typ.group(1) if typ else 'text'}")
    
    # Extract JS files and API endpoints
    js = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', r.text)
    print(f"  JS files: {js[:5]}")
    api_calls = re.findall(r'(["\'])(/api/[^\s"\']+)(\1)', r.text)
    print(f"  API calls in JS: {api_calls[:10]}")
except Exception as e:
    print(f"FSM: ERROR {str(e)[:200]}")
