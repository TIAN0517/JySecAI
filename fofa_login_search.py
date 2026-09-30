#!/usr/bin/env python3
"""
Phase 6b: FOFA search for login/admin endpoints on 119 systems.
Use FOFA's ability to search for specific paths and ports.
Also search for common 119 system patterns.
"""
import requests, json, base64, time, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FOFA_KEY = "dicl79nhrtolm07vqxk03fcqjyt4nvxu"
FOFA_BASE = "https://fofoapi.com/api/v1/search/all"

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
})

# Targeted queries for login/admin endpoints
queries = [
    # Search for login panels on 119 domain
    '"service119.tfd.gov.tw" inurl:login',
    '"service119.tfd.gov.tw" inurl:auth',
    '"service119.tfd.gov.tw" inurl:admin',
    '"service119.119.gov.taipei" inurl:login',
    '"taipeiciiis.119.gov.taipei" inurl:login',
    '"taipeiciiis-dashboard.119.gov.taipei" inurl:login',
    '"tpertc.tfd.gov.tw" inurl:login',
    '"epcr.tpf.gov.tw" inurl:login',
    '"epcr.tpf.gov.tw" inurl:auth',
    
    # Search for specific 119 endpoints
    'inurl:citizenCase',
    'inurl:genToken',
    'inurl:fetchServerData',
    'inurl:getUserToken',
    'inurl:caseList',
    'inurl:ohca',
    'inurl:pcdt',
    'inurl:vitalsign',
    
    # Search for EPCR components
    '"epcr" "login"',
    '"epcr" "auth"',
    '"vitalsignvideoserver"',
    '"PCDT" "login"',
    '"MerBridge"',
    '"mciServer"',
    '"monitorServer"',
    '"HospitalServer"',
    '"DoctorServer"',
    
    # Port-specific searches for 119 systems
    '"service119" port:443',
    '"service119" port:80',
    '"epcr.tpf" port:4000',
    '"epcr.tpf" port:4001',
    '"epcr.tpf" port:4002',
    '"epcr.tpf" port:4003',
    '"epcr.tpf" port:4004',
    '"epcr.tpf" port:4007',
    
    # Search for 119 login portals in Taiwan
    '"119" "login" site:gov.tw',
    '"119" "login" site:taipei.gov"',
    
    # Search for specific 119 dispatch system components
    '"caseList" "tfd"',
    '"caseList" "119"',
    '"citizenCase" "tfd"',
    '"citizenCase" "119"',
    
    # Search for Taipei 119 dashboard/admin
    '"taipeiciiis" inurl:login',
    '"taipeiciiis" inurl:admin',
    '"taipeiciiis" inurl:dashboard',
    '"af-search" 119.gov.taipei',
    '"fsm" 119.gov.taipei',
]

print("=" * 70)
print("FOFA TARGETED LOGIN ENDPOINT SEARCH")
print("=" * 70)

all_results = {}
for q in queries:
    enc = base64.b64encode(q.encode()).decode()
    url = f"{FOFA_BASE}?key={FOFA_KEY}&qbase64={enc}&full=true&page=1&pagesize=100"
    try:
        r = s.get(url, timeout=20, verify=False, allow_redirects=False)
        j = r.json()
        if j.get("error"):
            msg = j.get("errmsg", j.get("message", ""))
            if "fpoint" in msg.lower() or "point" in msg.lower():
                # Rate limited, try fofoapi.com
                url = f"https://fofoapi.com/api/v1/search/all?key={FOFA_KEY}&qbase64={enc}&full=true&page=1&pagesize=100"
                r = s.get(url, timeout=20, verify=False, allow_redirects=False)
                j = r.json()
                if j.get("error"):
                    msg = j.get("errmsg", j.get("message", ""))
                    print(f"[{q}] ERROR: {msg}")
                    continue
        
        results = j.get("results", [])
        size = j.get("size", len(results))
        if results:
            print(f"[{q}] {len(results)} results (total: {size})")
            all_results[q] = []
            for res in results[:10]:
                host = res[0] if len(res) > 0 else ""
                ip = res[1] if len(res) > 1 else ""
                port = res[2] if len(res) > 2 else ""
                extra = res[3:] if len(res) > 3 else []
                all_results[q].append({"host": host, "ip": ip, "port": port, "extra": extra})
                print(f"  -> {host} | {ip}:{port} | {extra}")
        else:
            print(f"[{q}] 0 results")
    except Exception as e:
        print(f"[{q}] Exception: {e}")
    time.sleep(1)

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

unique = {}
for q, results in all_results.items():
    for r in results:
        key = f"{r['ip']}:{r['port']}" if r['ip'] else r['host']
        if key not in unique:
            unique[key] = {"host": r['host'], "ip": r['ip'], "port": r['port'], "extra": r['extra'], "queries": [q]}
        else:
            if q not in unique[key]["queries"]:
                unique[key]["queries"].append(q)

print(f"\nTotal unique hosts: {len(unique)}")
for key, info in sorted(unique.items()):
    print(f"  {info['host']} | {info['ip']}:{info['port']} | {info['extra']} | queries: {info['queries']}")

output_file = f"/home/bossjy/.hermes/cache/scratch/fofa_login_search_{int(time.time())}.json"
with open(output_file, "w") as f:
    json.dump({"queries": all_results, "unique": unique}, f, indent=2, default=str, ensure_ascii=False)
print(f"\n[*] Results saved to: {output_file}")
