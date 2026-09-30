#!/usr/bin/env python3
"""
Phase 4 COMPLETE: FOFA carpet search using fofoapi.com/api/v1/search/all with key=dicl...
Comprehensive search for ALL 119 dispatch system login endpoints across Taiwan gov domains.
"""
import requests
import json
import base64
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FOFA_URL = "https://fofoapi.com/api/v1/search/all"
FOFA_KEY = "dicl79nhrtolm07vqxk03fcqjyt4nvxu"

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})

def fofa_search(query, pages=1):
    """Search FOFA and return all results."""
    enc = base64.b64encode(query.encode()).decode()
    all_results = []
    
    for page in range(1, pages + 1):
        url = f"{FOFA_URL}?key={FOFA_KEY}&qbase64={enc}&page={page}&pagesize=100&full=true"
        try:
            r = s.get(url, timeout=30, verify=False)
            if r.status_code == 200:
                data = r.json()
                if data.get("error"):
                    err = data.get("errmsg", data.get("message", ""))
                    print(f"    API Error: {err}")
                    return all_results
                results = data.get("results", [])
                size = data.get("size", len(results))
                print(f"    Page {page}: {len(results)} results (total: {size})")
                all_results.extend(results)
                if len(results) < 100 or page >= pages:
                    break
                time.sleep(1)
            else:
                print(f"    HTTP {r.status_code}")
        except Exception as e:
            print(f"    Error: {e}")
    return all_results

# Comprehensive search queries for 119 dispatch system login/ingress endpoints
queries = [
    # Direct domain searches
    "service119.tfd.gov.tw",
    "appservice119.tfd.gov.tw",
    "119.gov.taipei",
    "epcr.tpf.gov.tw",
    "tpertc.tfd.gov.tw",
    "tpf.gov.tw",
    "tfd.gov.tw",
    "emic.gov.tw",
    "bear.emic.gov.tw",
    
    # Service119 login/auth/API endpoints
    "service119.tfd.gov.tw /citizen/auth/genToken",
    "service119.tfd.gov.tw /citizenCase",
    "service119.tfd.gov.tw /citizenCase/caseList",
    "service119.tfd.gov.tw /auth/fetchServerData",
    "service119.tfd.gov.tw /api/getUserToken",
    "service119.tfd.gov.tw /citizenCase/initUserCategory",
    "service119.tfd.gov.tw login",
    "service119.tfd.gov.tw auth",
    "service119.tfd.gov.tw api",
    
    # EPCR system
    "epcr.tpf.gov.tw",
    "epcr.tpf.gov.tw :4000",
    "epcr.tpf.gov.tw :4001",
    "epcr.tpf.gov.tw :4004",
    "vitalsignvideoserver",
    "epcr.tpf.gov.tw ohca",
    "epcr.tpf.gov.tw pcdt",
    
    # Taiwan 119 broad search
    "台北 119 dispatch",
    "service119",
    "119 caseList",
    "119 citizenCase",
    "119 ohca",
    
    # Login pages specific
    "inurl:login site:tfd.gov.tw",
    "inurl:login site:tpf.gov.tw",
    "inurl:genToken",
    "inurl:getUserToken",
    "inurl:auth site:gov.tw 119",
    
    # Admin/portal
    "inurl:admin 119 site:gov.tw",
    "inurl:portal tfd",
    "inurl:dashboard 119 site:gov.tw",
    
    # API endpoints
    "inurl:api 119 site:gov.tw",
    "inurl:api service119",
    "inurl:api epcr",
    "inurl:api ohca",
    
    # OHCA / medical
    "inurl:ohca",
    "inurl:pcdt",
    "inurl:vitalsign",
    "ohca site:gov.tw",
    
    # Emergency dispatch
    "inurl:emergency dispatch",
    "inurl:caseList",
    "inurl:citizenCase",
    "caseList site:tw",
    
    # 119 specific government
    "119 site:tfd.gov.tw",
    "119 site:tpf.gov.tw",
    "119 site:gov.taipei.tw",
    
    # WebSocket / real-time
    "inurl:websocket 119",
    "inurl:socket.io service119",
    "socket.io service119",
    
    # Fire department systems
    "tfd fire dispatch",
    "tfd emergency dispatch",
    "fire department 119 taiwan",
    
    # EMS / ambulance
    "ems taiwan 119",
    "ambulance dispatch site:tw",
    
    # Additional government 119
    "119.gov.tw",
    "119.gov.tw login",
    "119.gov.tw api",
    
    # EPCR specific
    "epcr taiwan",
    "epcr login site:tw",
    "EPCR site:gov.tw",
]

print("=" * 70)
print("FOFA CARPET SEARCH - COMPLETE")
print("=" * 70)
print(f"[*] Endpoint: {FOFA_URL}")
print(f"[*] API key: {FOFA_KEY[:8]}...{FOFA_KEY[-4:]}")
print(f"[*] Total queries: {len(queries)}")
print()

all_findings = {}
unique_hosts = {}

for i, q in enumerate(queries):
    print(f"\n[{i+1}/{len(queries)}] Query: \"{q}\"")
    results_list = fofa_search(q, pages=1)
    
    if results_list:
        all_findings[q] = results_list
        for r in results_list:
            if len(r) >= 3:
                host = r[0]
                ip = r[1]
                port = r[2]
                extra = r[3:] if len(r) > 3 else []
                key = f"{ip}:{port}"
                if key not in unique_hosts:
                    unique_hosts[key] = {"host": host, "ip": ip, "port": port, "extra": extra, "sources": [q]}
                else:
                    if q not in unique_hosts[key]["sources"]:
                        unique_hosts[key]["sources"].append(q)
                print(f"  -> {host} | {ip}:{port} | {extra}")
    else:
        print(f"  -> No results")
    time.sleep(0.3)

# Save full results
output_file = f"/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/fofa_carpet_complete_{int(time.time())}.json"
with open(output_file, "w") as f:
    json.dump({
        "api_endpoint": FOFA_URL,
        "api_key": FOFA_KEY,
        "total_queries": len(queries),
        "queries_used": queries,
        "all_results": all_findings,
        "unique_hosts": unique_hosts,
    }, f, indent=2, default=str, ensure_ascii=False)

print(f"\n{'=' * 70}")
print(f"SUMMARY: {len(unique_hosts)} unique IP:port combos from {len(all_findings)} queries")
print(f"{'=' * 70}")
for key, info in sorted(unique_hosts.items()):
    print(f"  {info['host']} | {key} | extra: {info['extra']} | from: {info['sources']}")
print(f"\n[*] Full results saved to: {output_file}")
