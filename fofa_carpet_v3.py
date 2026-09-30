#!/usr/bin/env python3
"""
Phase 4b: FOFA carpet search - corrected API endpoint.
The working endpoint was: https://api.fofa.info/v1/search/all (NOT /api/v1/...)
Also try fofoapi.com with correct path.
"""
import requests
import json
import base64
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FOFA_KEY = "dicl79nhrtolm07vqxk03fcqjyt4nvxu"

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})

def fofa_search_v1(query, pages=1):
    """Search FOFA via api.fofa.info/v1/search/all (the working endpoint)."""
    enc = base64.b64encode(query.encode()).decode()
    all_results = []
    
    # Working endpoint from phase 3f
    endpoints = [
        f"https://api.fofa.info/v1/search/all?key={FOFA_KEY}&qbase64={enc}&page={{page}}&pagesize=100",
    ]
    
    for url_template in endpoints:
        for page in range(1, pages + 1):
            url = url_template.format(page=page)
            try:
                r = s.get(url, timeout=30, verify=False)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("error"):
                        err = data.get("errmsg", data.get("message", ""))
                        if "fpoint" in err.lower() or "key" in err.lower() or "token" in err.lower():
                            print(f"    API key/auth error: {err}")
                            return all_results
                        print(f"    Error: {err}")
                        continue
                    results = data.get("results", [])
                    total = data.get("size", len(results))
                    print(f"    [{url.split('/')[3]}] Page {page}: {len(results)} results (total: {total})")
                    all_results.extend(results)
                    if len(results) < 100 or total <= len(all_results):
                        break
                    time.sleep(1)
                else:
                    print(f"    HTTP {r.status_code}: {r.text[:200]}")
            except Exception as e:
                print(f"    Error: {e}")
    
    return all_results

def main():
    queries = [
        "service119.tfd.gov.tw",
        "appservice119.tfd.gov.tw",
        "119.gov.taipei",
        "epcr.tpf.gov.tw",
        "tpertc.tfd.gov.tw",
        "tpf.gov.tw",
        "tfd.gov.tw",
        "service119.tfd.gov.tw /citizen/auth/genToken",
        "service119.tfd.gov.tw /citizenCase",
        "service119.tfd.gov.tw /auth/fetchServerData",
        "service119.tfd.gov.tw /api/getUserToken",
        "epcr.tpf.gov.tw",
        "vitalsignvideoserver",
        "台北 119 dispatch",
        "service119 login",
        "service119 epcr",
        "119 caseList",
        "119 citizenCase",
        "119 ohca",
        "119 emergency dispatch site:tw",
    ]
    
    print("=" * 70)
    print("FOFA CARPET SEARCH (api.fofa.info/v1)")
    print("=" * 70)
    print(f"[*] API key: {FOFA_KEY[:8]}...{FOFA_KEY[-4:]}")
    print()
    
    all_findings = {}
    
    for q in queries:
        print(f"\n[*] Query: \"{q}\"")
        results_list = fofa_search_v1(q, pages=1)
        if results_list:
            all_findings[q] = results_list
            for r in results_list[:10]:
                host = r[0] if len(r) > 0 else ""
                ip = r[1] if len(r) > 1 else ""
                port = r[2] if len(r) > 2 else ""
                rest = r[3:] if len(r) > 3 else []
                print(f"  -> {host} | {ip}:{port} | {rest}")
        else:
            print(f"  -> No results")
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY - Unique hosts:")
    print("=" * 70)
    
    unique_hosts = {}
    for q, results_list in all_findings.items():
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
                    unique_hosts[key]["sources"].append(q)
    
    for key, info in sorted(unique_hosts.items()):
        print(f"  {info['host']} | {key} | extra: {info['extra']} | from: {info['sources'][:3]}")
    
    # Save
    output_file = f"/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/fofa_carpet_v2_{int(time.time())}.json"
    with open(output_file, "w") as f:
        json.dump({
            "api_key": FOFA_KEY,
            "queries": queries,
            "all_results": all_findings,
            "unique_hosts": unique_hosts,
        }, f, indent=2, default=str, ensure_ascii=False)
    print(f"\n[*] Results saved to: {output_file}")

if __name__ == "__main__":
    main()
