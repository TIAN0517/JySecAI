#!/usr/bin/env python3
"""
Phase 4: Complete FOFA carpet search using the discovered API key.
The token 'dicl79nhrtolm07vqxk03fcqjyt4nvxu' IS the FOFA API key (fofa.info v1 API).
Searches for all 119 dispatch system login endpoints across Taiwan gov domains.
"""
import requests
import json
import base64
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FOFA_API = "https://api.fofa.info/v1/search/all"
FOFA_KEY = "dicl79nhrtolm07vqxk03fcqjyt4nvxu"

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})

def fofa_search(query, pages=1):
    """Search FOFA and return all results across pages."""
    enc = base64.b64encode(query.encode()).decode()
    all_results = []
    
    for page in range(1, pages + 1):
        url = f"{FOFA_API}?key={FOFA_KEY}&qbase64={enc}&page={page}&pagesize=100"
        try:
            r = s.get(url, timeout=30, verify=False)
            if r.status_code == 200:
                data = r.json()
                if data.get("error"):
                    print(f"    Error: {data.get('errmsg', data.get('message', ''))}")
                    return all_results
                results = data.get("results", [])
                total = data.get("size", len(results))
                print(f"    Page {page}: {len(results)} results (total: {total})")
                all_results.extend(results)
                if len(results) < 100:
                    break  # No more results
                time.sleep(1)  # Rate limit
            else:
                print(f"    HTTP {r.status_code}")
        except Exception as e:
            print(f"    Error: {e}")
    return all_results

def main():
    results = {}
    
    # Comprehensive search queries for 119 dispatch system login endpoints
    queries = [
        # Direct domain searches
        "service119.tfd.gov.tw",
        "appservice119.tfd.gov.tw",
        "119.gov.taipei",
        "epcr.tpf.gov.tw",
        "tpertc.tfd.gov.tw",
        "tpf.gov.tw",
        "tfd.gov.tw",
        
        # Service119 login/auth endpoints
        "service119.tfd.gov.tw service119",
        "service119.tfd.gov.tw /citizen/auth/genToken",
        "service119.tfd.gov.tw /citizenCase",
        "service119.tfd.gov.tw /auth/fetchServerData",
        "service119.tfd.gov.tw /api/getUserToken",
        
        # EPCR system
        "epcr.tpf.gov.tw",
        "epcr.tpf.gov.tw :4000",
        "epcr.tpf.gov.tw :4001",
        "epcr.tpf.gov.tw :4004",
        "vitalsignvideoserver",
        
        # Broad Taiwan 119 search
        "台北 119 dispatch",
        "\"119\" \"tfd.gov.tw\"",
        "\"service119\"",
        
        # Login pages
        "inurl:login \"119\"",
        "inurl:login tfd.gov.tw",
        "inurl:login tpf.gov.tw",
        "inurl:genToken",
        "inurl:getUserToken",
        
        # Admin/portal
        "inurl:admin \"119\"",
        "inurl:portal \"tfd\"",
        "inurl:dashboard \"119\"",
        
        # WebSocket / real-time
        "inurl:websocket 119",
        "inurl:socket.io service119",
        
        # API endpoints
        "inurl:api \"119\" site:gov.tw",
        "inurl:api service119",
        "inurl:api epcr",
        
        # OHCA / medical
        "inurl:ohca",
        "inurl:pcdt",
        "inurl:vitalsign",
        "\"OHCA\" site:gov.tw",
        
        # Emergency dispatch
        "inurl:emergency \"dispatch\"",
        "inurl:caseList",
        "inurl:citizenCase",
        "\"caseList\" site:tw",
    ]
    
    print("=" * 70)
    print("FOFA CARPET SEARCH FOR TAIWAN 119 DISPATCH SYSTEMS")
    print("=" * 70)
    print(f"[*] Using FOFA API key: {FOFA_KEY[:8]}...{FOFA_KEY[-4:]}")
    print()
    
    all_findings = {}
    
    for q in queries:
        print(f"\n[*] Query: \"{q}\"")
        results_list = fofa_search(q, pages=1)
        if results_list:
            all_findings[q] = results_list
            for r in results_list:
                host = r[0] if len(r) > 0 else ""
                ip = r[1] if len(r) > 1 else ""
                port = r[2] if len(r) > 2 else ""
                print(f"  -> {host} | {ip}:{port}")
        else:
            print(f"  -> No results")
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 70)
    print("FOFA SEARCH SUMMARY")
    print("=" * 70)
    
    unique_hosts = set()
    unique_ips = set()
    for q, results_list in all_findings.items():
        for r in results_list:
            if len(r) >= 3:
                host = r[0]
                ip = r[1]
                port = r[2]
                unique_hosts.add(host)
                unique_ips.add(f"{ip}:{port}")
    
    print(f"Total unique hosts found: {len(unique_hosts)}")
    print(f"Total unique IP:port combos: {len(unique_ips)}")
    print()
    
    for q, results_list in all_findings.items():
        if results_list:
            print(f"\nQuery: \"{q}\" -> {len(results_list)} results")
            for r in results_list:
                if len(r) >= 3:
                    print(f"  {r[0]} | {r[1]}:{r[2]}")
                elif len(r) >= 2:
                    print(f"  {r[0]} | {r[1]}")
                else:
                    print(f"  {r[0] if r else '??'}")
    
    # Save all results
    output_file = f"/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/fofa_carpet_search_{int(time.time())}.json"
    with open(output_file, "w") as f:
        json.dump({
            "api_key": FOFA_KEY,
            "queries": queries,
            "results": all_findings,
            "unique_hosts": list(unique_hosts),
            "unique_ips": list(unique_ips),
        }, f, indent=2, default=str, ensure_ascii=False)
    print(f"\n[*] Full results saved to: {output_file}")
    
    return all_findings

if __name__ == "__main__":
    main()
