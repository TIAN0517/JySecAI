#!/usr/bin/env python3
"""
Phase 5: Subdomain carpet search using FOFA API + subfinder/amass.
Focus on enumerating ALL subdomains for the 119 dispatch system domains.
"""
import requests, json, base64, time, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FOFA_KEY = "dicl79nhrtolm07vqxk03fcqjyt4nvxu"

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})

def fofa_search_full(query, pages=5):
    """Search FOFA with full result metadata."""
    enc = base64.b64encode(query.encode()).decode()
    all_results = []
    
    for page in range(1, pages + 1):
        url = f"https://api.fofa.info/v1/search/all?key={FOFA_KEY}&qbase64={enc}&page={page}&pagesize=100&full=true"
        try:
            r = s.get(url, timeout=30, verify=False)
            data = r.json()
            if data.get("error"):
                if data.get("errmsg") and "fpoint" in data["errmsg"].lower():
                    # Switch to fofoapi.com
                    url = f"https://fofoapi.com/api/v1/search/all?key={FOFA_KEY}&qbase64={enc}&page={page}&pagesize=100&full=true"
                    r = s.get(url, timeout=30, verify=False)
                    data = r.json()
                    if data.get("error"):
                        print(f"  [FOFA ERROR] {data}")
                        break
                else:
                    print(f"  [FOFA ERROR] {data}")
                    break
            results = data.get("results", [])
            size = data.get("size", len(results))
            if not results:
                break
            print(f"  Page {page}: {len(results)} results (total: {size})")
            all_results.extend(results)
            if len(results) < 100:
                break
            time.sleep(1)
        except Exception as e:
            print(f"  Error: {e}")
    return all_results

# Focus queries on subdomain discovery
subdomain_queries = [
    # Service119 subdomains
    "service119.tfd.gov.tw",
    "appservice119.tfd.gov.tw",
    
    # 119.gov.taipei subdomains (CIIIS)
    "119.gov.taipei",
    
    # EPCR
    "epcr.tpf.gov.tw",
    
    # TFD subdomains
    "tfd.gov.tw",
    
    # TPF subdomains
    "tpf.gov.tw",
    
    # TPERTC (telemedicine)
    "tpertc.tfd.gov.tw",
    
    # EMIC
    "emic.gov.tw",
    
    # Specific login/admin endpoint searches
    "tfd.gov.tw inurl:login",
    "tfd.gov.tw inurl:auth",
    "tpf.gov.tw inurl:login",
    "tpf.gov.tw inurl:auth",
    "119.gov.taipei inurl:login",
    "119.gov.taipei inurl:auth",
    "service119 inurl:login",
    "service119 inurl:auth",
    
    # Port-specific searches for 119 systems
    "service119.tfd.gov.tw:443",
    "service119.119.gov.taipei",
    "taipeiciiis.119.gov.taipei",
    "taipeiciiis-dashboard.119.gov.taipei",
    
    # EPCR port searches
    "epcr.tpf.gov.tw:4000",
    "epcr.tpf.gov.tw:4001",
    "epcr.tpf.gov.tw:4002",
    "epcr.tpf.gov.tw:4003",
    "epcr.tpf.gov.tw:4004",
    "epcr.tpf.gov.tw:4005",
    "epcr.tpf.gov.tw:4006",
    "epcr.tpf.gov.tw:4007",
    "epcr.tpf.gov.tw:4008",
    
    # Broad Taiwan emergency/119
    "台灣 119 救譫",
    "台灣 119 火災",
    "台灣 緊急救護",
    "臺北 119 調度",
    "消防 119 api",
    "EMS Taiwan 119",
    "EPCR Taiwan",
    
    # Port scan style searches
    "ip_country:\"TW\" port:443 http:",
    "ip_country:\"TW\" port:80 http:",
    "ip_country:\"TW\" port:8080 http:",
    "ip_country:\"TW\" port:8443 http:",
]

print("=" * 70)
print("FOFA SUBDOMAIN CARPET SEARCH")
print("=" * 70)
print(f"[*] API key: {FOFA_KEY[:8]}...{FOFA_KEY[-4:]}")
print(f"[*] Queries: {len(subdomain_queries)}")
print()

all_results = {}
for q in subdomain_queries:
    print(f"\n[*] Query: \"{q}\"")
    results = fofa_search_full(q, pages=3)
    if results:
        all_results[q] = results
        for r in results[:5]:  # Show first 5
            fields = r if isinstance(r, list) else [str(r)]
            host = fields[0] if len(fields) > 0 else ""
            ip = fields[1] if len(fields) > 1 else ""
            port = fields[2] if len(fields) > 2 else ""
            extra = fields[3:] if len(fields) > 3 else []
            print(f"  -> {host} | {ip}:{port} | {extra}")
        if len(results) > 5:
            print(f"  ... and {len(results)-5} more")
    else:
        print(f"  -> No results")
    time.sleep(0.5)

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

unique = {}
for q, results in all_results.items():
    for r in results:
        fields = r if isinstance(r, list) else [str(r)]
        host = fields[0] if len(fields) > 0 else ""
        ip = fields[1] if len(fields) > 1 else ""
        port = fields[2] if len(fields) > 2 else ""
        key = f"{ip}:{port}" if ip else host
        if key not in unique:
            unique[key] = {"host": host, "ip": ip, "port": port, "extra": fields[3:] if len(fields) > 3 else [], "queries": [q]}
        else:
            if q not in unique[key]["queries"]:
                unique[key]["queries"].append(q)

print(f"\nTotal unique hosts: {len(unique)}")
for key, info in sorted(unique.items()):
    host_str = f"{info['host']} | " if info['host'] else ""
    print(f"  {host_str}{info['ip']}:{info['port']} | extra: {info['extra']} | queries: {info['queries']}")

# Save
output_file = f"/home/bossjy/.hermes/cache/scratch/fofa_subdomain_carpet_{int(time.time())}.json"
with open(output_file, "w") as f:
    json.dump({"queries": all_results, "unique": unique}, f, indent=2, default=str, ensure_ascii=False)
print(f"\n[*] Results saved to: {output_file}")
