#!/usr/bin/env python3
"""
Phase 7: Probe login endpoints on the most critical 119 system subdomains.
Found via subfinder + FOFA:
- appservice119.tfd.gov.tw (Apache+PHP)
- service119.119.gov.taipei
- fsm.119.gov.taipei
- www.af-search.119.gov.taipei
- taipeiciiis.119.gov.taipei
- taipeiciiis-dashboard.119.gov.taipi
- tpertc.tfd.gov.tw
- epcr.tpf.gov.tw
- mer2.tpf.gov.tw
- 119appcaseapi.tpf.gov.tw
- 119api.tpf.gov.tw
"""
import requests, json, time, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/json,*/*",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})

# Critical 119 system hosts to probe for login endpoints
critical_hosts = [
    # service119 system (already known)
    "https://service119.tfd.gov.tw/service119",
    
    # appservice119 - Apache+PHP backend
    "https://appservice119.tfd.gov.tw",
    
    # 119.gov.taipei subdomains
    "https://www.119.gov.taipei",
    "https://fsm.119.gov.taipei",
    "https://www.af-search.119.gov.taipei",
    "https://service119.119.gov.taipei",
    "https://taipeiciiis.119.gov.taipei",
    "https://taipeiciiis-dashboard.119.gov.taipei",
    "https://camcall.119.gov.taipei",
    "https://bnoc.119.gov.taipei",
    "https://pnoc.119.gov.taipei",
    "https://tfdus.119.gov.taipei",
    "https://www.firesignal.119.gov.taipei",
    "https://www.rfd119.119.gov.taipei",
    "https://www.tpeusar.119.gov.taipei",
    "https://www.rfd119en.119.gov.taipei",
    "https://english.119.gov.taipei",
    "https://taipeiciiis-dt.119.gov.taipei",
    
    # tpf.gov.tw 119-related subdomains
    "https://epcr.tpf.gov.tw",
    "https://mer2.tpf.gov.tw",
    "https://119api.tpf.gov.tw",
    "https://119appapi.tpf.gov.tw",
    "https://119appcaseapi.tpf.gov.tw",
    "https://119appcasefile.tpf.gov.tw",
    "https://119epcrapi.tpf.gov.tw",
    "https://119firecaseapi.tpf.gov.tw",
    "https://smartems.tpf.gov.tw",
    "https://mntfd119web.tpf.gov.tw",
    "https://safe.tpf.gov.tw",
    "https://safeap.tpf.gov.tw",
    "https://checkap.tpf.gov.tw",
    "https://checkapp.tpf.gov.tw",
    
    # tfd.gov.tw fire-related
    "https://trauma.tfd.gov.tw",
    "https://gis119.tfd.gov.tw",
    "https://taipeiepcr.tfd.gov.tw",
    "https://eoc.tdprc2.tfd.gov.tw",
    "https://turnserver.tfd.gov.tw",
    "https://tpertc.tfd.gov.tw",
    
    # epcr tpf ports
    "https://epcr.tpf.gov.tw:4000",
    "https://epcr.tpf.gov.tw:4001",
    "https://epcr.tpf.gov.tw:4002",
    "https://epcr.tpf.gov.tw:4003",
    "https://epcr.tpf.gov.tw:4004",
    "https://epcr.tpf.gov.tw:4005",
    "https://epcr.tpf.gov.tw:4006",
    "https://epcr.tpf.gov.tw:4007",
]

# Login endpoint probes
login_paths = [
    "/", "/index", "/index.html", "/login", "/Login", "/admin/login",
    "/api/login", "/auth/login", "/auth/genToken", "/citizen/auth/genToken",
    "/auth/fetchServerData", "/api/getUserToken", "/user/login",
    "/api/v1/login", "/api/v1/auth", "/oauth/token", "/oauth2/authorize",
    "/sso/login", "/cas/login", "/j_spring_security_check",
    "/admin", "/console", "/dashboard", "/management",
    "/swagger", "/swagger-ui.html", "/api-docs", "/v1/api-docs",
    "/config", "/config.json", "/robots.txt", "/favicon.ico",
    "/.well-known/", "/security.txt", "/.env",
    "/index.php", "/index.jsp", "/index.asp",
    "/caseList", "/caseList.jsp",
    "/citizenCase", "/citizenCase/caseList",
    "/dispatch", "/dispatchLogin",
    "/ambulance", "/ems",
    "/websocket", "/socket.io/",
    "/mer2", "/merBridge",
    "/vitalsign", "/vitalsignvideoserver",
]

print("=" * 70)
print("LOGIN ENDPOINT DISCOVERY - CRITICAL 119 HOSTS")
print("=" * 70)

results = {}
for base in critical_hosts:
    print(f"\n[*] Probing: {base}")
    host_results = []
    
    for path in login_paths:
        url = f"{base}{path}"
        try:
            r = s.get(url, timeout=10, verify=False, allow_redirects=False)
            status = r.status_code
            length = len(r.text) if r.text else 0
            server = r.headers.get("Server", "").strip()[:80]
            ct = r.headers.get("Content-Type", "").strip()[:80]
            location = r.headers.get("Location", "").strip()[:150]
            
            if status != 404 or (status == 200 and length > 100):
                snippet = r.text[:200].replace('\n', ' ').replace('\r', '')
                host_results.append({
                    "path": path, "url": url, "status": status,
                    "length": length, "server": server, "ct": ct,
                    "location": location, "body": snippet
                })
                
                marker = ""
                if status in [200, 301, 302, 307, 308]:
                    marker = " <-- "
                    if status in [301, 302]:
                        marker += f"redirect -> {location}"
                    elif status == 200:
                        marker += "OK"
                elif status in [401, 403]:
                    marker = f" (auth: {status})"
                
                print(f"  [{status}] {path} ({length}b) [{server[:40]}]{marker}")
                if marker.startswith(" <-- "):
                    if r.text:
                        print(f"    Body: {snippet[:120]}")
        except requests.exceptions.SSLError:
            pass
        except Exception as e:
            err = str(e)
            if "Connection refused" in err or "timed out" in err or "Name or service" in err:
                pass
            else:
                print(f"  [ERR] {path}: {type(e).__name__}: {err[:80]}")
    
    results[base] = host_results
    time.sleep(0.2)

# Summary
print("\n" + "=" * 70)
print("INTERESTING ENDPOINTS (200/30x with content, 401/403)")
print("=" * 70)

interesting_count = 0
for base, findings in results.items():
    interesting = [f for f in findings if f["status"] in [200, 301, 302, 307, 308, 401, 403]]
    if interesting:
        print(f"\n{base}:")
        for f in interesting:
            interesting_count += 1
            marker = ""
            if f["status"] in [200, 301, 302, 307, 308]:
                marker = "<-- LIVE"
                if f["status"] in [301, 302]:
                    marker += f"-> {f['location']}"
            elif f["status"] in [401, 403]:
                marker = f"<-- {f['status']} (auth required)"
            print(f"  [{f['status']}] {f['path']} ({f['length']}b) [{f['server'][:40]}] {marker}")
            if f["body"]:
                print(f"    -> {f['body'][:100]}")

print(f"\nTotal interesting endpoints: {interesting_count}")

output_file = f"/home/bossjy/.hermes/cache/scratch/login_critical_{int(time.time())}.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=2, default=str, ensure_ascii=False)
print(f"\n[*] Results saved to: {output_file}")
