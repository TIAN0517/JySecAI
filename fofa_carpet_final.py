#!/usr/bin/env python3
"""Phase 5: Complete FOFA subdomain carpet search."""
import requests, json, base64, time, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FOFA_KEY = "dicl79nhrtolm07vqxk03fcqjyt4nvxu"
FOFA_BASE = "https://fofoapi.com/api/v1/search/all"

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
})

queries = [
    "service119.tfd.gov.tw",
    "appservice119.tfd.gov.tw",
    "119.gov.taipei",
    "epcr.tpf.gov.tw",
    "tfd.gov.tw",
    "tpf.gov.tw",
    "tpertc.tfd.gov.tw",
    "emic.gov.tw",
    "tfd.gov.tw inurl:login",
    "tfd.gov.tw inurl:auth",
    "tpf.gov.tw inurl:login",
    "tpf.gov.tw inurl:auth",
    "119.gov.taipei inurl:login",
    "119.gov.taipei inurl:auth",
    "service119 inurl:login",
    "service119 inurl:auth",
    "service119.119.gov.taipei",
    "taipeiciiis.119.gov.taipei",
    "taipeiciiis-dashboard.119.gov.taipei",
    "epcr.tpf.gov.tw:4000",
    "epcr.tpf.gov.tw:4001",
    "epcr.tpf.gov.tw:4002",
    "epcr.tpf.gov.tw:4003",
    "epcr.tpf.gov.tw:4004",
    "epcr.tpf.gov.tw:4005",
    "epcr.tpf.gov.tw:4006",
    "epcr.tpf.gov.tw:4007",
    "epcr.tpf.gov.tw:4008",
    "台灣 119 救譫",
    "台灣 119 火災",
    "台灣 緊急救護",
    "臺北 119 調度",
    "消防 119 api",
    "ip_country:\"TW\" port:443 http:",
    "ip_country:\"TW\" port:80 http:",
]

print("=" * 70)
print("FOFA SUBDOMAIN CARPET SEARCH")
print("=" * 70)
print(f"API key: {FOFA_KEY[:8]}...{FOFA_KEY[-4:]}")
print(f"Queries: {len(queries)}")
print()

all_results = {}
for q in queries:
    enc = base64.b64encode(q.encode()).decode()
    url = f"{FOFA_BASE}?key={FOFA_KEY}&qbase64={enc}&full=true&page=1&pagesize=100"
    try:
        r = s.get(url, timeout=20, verify=False, allow_redirects=False)
        if r.status_code == 200:
            j = r.json()
            if j.get("error"):
                print(f"[{q}] ERROR: {j.get('errmsg', j.get('message', ''))}")
            else:
                results = j.get("results", [])
                size = j.get("size", len(results))
                print(f"[{q}] {len(results)} results (total: {size})")
                if results:
                    all_results[q] = results
                    for res in results[:5]:
                        host = res[0] if len(res) > 0 else ""
                        ip = res[1] if len(res) > 1 else ""
                        port = res[2] if len(res) > 2 else ""
                        extra = res[3:] if len(res) > 3 else []
                        print(f"  -> {host} | {ip}:{port} | {extra}")
                    if len(results) > 5:
                        print(f"  ... +{len(results)-5} more")
        else:
            print(f"[{q}] HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"[{q}] Exception: {e}")
    time.sleep(0.5)

# Summary
print("\n" + "=" * 70)
print("SUMMARY - All unique hosts")
print("=" * 70)

unique = {}
for q, results in all_results.items():
    for r in results:
        host = r[0] if len(r) > 0 else ""
        ip = r[1] if len(r) > 1 else ""
        port = r[2] if len(r) > 2 else ""
        extra = r[3:] if len(r) > 3 else []
        key = f"{ip}:{port}" if ip else host
        if key not in unique:
            unique[key] = {"host": host, "ip": ip, "port": port, "extra": extra, "queries": [q]}
        else:
            if q not in unique[key]["queries"]:
                unique[key]["queries"].append(q)

print(f"\nTotal unique hosts: {len(unique)}")
for key, info in sorted(unique.items()):
    host_str = f"{info['host']} | " if info['host'] else ""
    extra_str = " | ".join(info['extra']) if info['extra'] else ""
    q_str = ", ".join(info['queries'])
    print(f"  {host_str}{info['ip']}:{info['port']} | extra: [{extra_str}] | queries: [{q_str}]")

output_file = f"/home/bossjy/.hermes/cache/scratch/fofa_carpet_final.json"
with open(output_file, "w") as f:
    json.dump({"queries": all_results, "unique": unique}, f, indent=2, default=str, ensure_ascii=False)
print(f"\n[*] Results saved to: {output_file}")
