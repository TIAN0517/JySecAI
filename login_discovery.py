#!/usr/bin/env python3
"""
Phase 6: Login endpoint discovery on 119 dispatch system hosts.
Target the key hosts found in FOFA carpet search, probe for login panels.
Also do subdomain enumeration on the key domains.
"""
import requests, json, base64, time, urllib3
import subprocess
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/json,*/*",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})

# Key 119 dispatch system hosts from FOFA results
key_hosts = [
    "service119.tfd.gov.tw",
    "appservice119.tfd.gov.tw",
    "www.119.gov.taipei",
    "service119.119.gov.taipei",
    "taipeiciiis.119.gov.taipei",
    "taipeiciiis-dashboard.119.gov.taipei",
    "tpertc.tfd.gov.tw",
    "tpertc.tfd.gov.tw:8787",
    "210.69.43.114:8787",
    "210.69.43.103:443",
    "210.69.43.112:443",
    "210.69.43.127:443",
    "210.69.43.129:443",
    "118.163.107.93:4000",
    "118.163.107.93:4001",
    "118.163.107.93:4002",
    "118.163.107.93:4003",
    "118.163.107.93:4004",
    "118.163.107.93:4005",
    "118.163.107.93:4006",
    "118.163.107.93:4007",
    "fsm.119.gov.taipei",
    "www.af-search.119.gov.taipei",
    "tdprc2.tfd.gov.tw:9527",
    "tdprc2.tfd.gov.tw:9530",
    "210.69.42.18:9000",
    "101.3.0.57:3389",
]

# Login endpoint patterns to probe
login_paths = [
    "/login",
    "/Login",
    "/LOGIN",
    "/admin/login",
    "/adminLogin",
    "/user/login",
    "/api/login",
    "/auth/login",
    "/auth/genToken",
    "/citizen/auth/genToken",
    "/auth/fetchServerData",
    "/api/getUserToken",
    "/index.php/Admin/Login",
    "/admin",
    "/admin/index",
    "/management",
    "/console",
    "/dashboard",
    "/login.jsp",
    "/login.aspx",
    "/login.php",
    "/login.html",
    "/index.asp",
    "/index.php",
    "/api/v1/login",
    "/api/v1/auth",
    "/api/auth/login",
    "/gateway/auth",
    "/oauth/token",
    "/oauth2/authorize",
    "/ssoserver/login",
    "/sso/login",
    "/cas/login",
    "/j_spring_security_check",
    "/.well-known/",
    "/config",
    "/config.json",
    "/swagger",
    "/swagger-ui",
    "/swagger-ui.html",
    "/v1/api-docs",
    "/api-docs",
    "/openapi.json",
    "/robots.txt",
    "/favicon.ico",
]

print("=" * 70)
print("LOGIN ENDPOINT DISCOVERY ON 119 SYSTEM HOSTS")
print("=" * 70)

results = {}
for host in key_hosts:
    # Determine protocol
    if ":443" in host:
        proto = "https"
        base = f"https://{host.replace(':443', '')}"
    elif ":8787" in host or ":80" in host:
        proto = "http"
        base = f"http://{host.replace(':80', '')}"
    elif ":9527" in host or ":9530" in host or ":18888" in host or ":9000" in host or ":3389" in host:
        proto = "http"
        base = f"http://{host}"
    else:
        proto = "https"
        base = f"https://{host}"
    
    print(f"\n[*] Probing: {base}")
    host_results = []
    
    for path in login_paths:
        url = f"{base}{path}"
        try:
            r = s.get(url, timeout=10, verify=False, allow_redirects=False)
            status = r.status_code
            length = len(r.text) if r.text else 0
            server = r.headers.get("Server", "").strip()[:50]
            content_type = r.headers.get("Content-Type", "").strip()[:50]
            
            # Mark interesting responses
            interesting = ""
            if status in [200, 301, 302, 307, 308]:
                interesting = " <-- INTERESTING"
            elif status in [400, 401, 403]:
                interesting = " (auth/protection)"
            
            if status != 404 and length > 0:
                # Get a snippet of the body
                body_snippet = r.text[:150].replace('\n', ' ').replace('\r', '')
                host_results.append({
                    "url": url,
                    "status": status,
                    "length": length,
                    "server": server,
                    "content_type": content_type,
                    "body": body_snippet,
                    "interesting": bool(interesting),
                })
                print(f"  [{status}] {path} ({length}b){interesting}")
                if status in [200, 301, 302]:
                    print(f"    Server: {server}")
                    print(f"    CT: {content_type}")
                    if len(body_snippet) > 0:
                        print(f"    Body: {body_snippet[:100]}")
                elif status in [401, 403]:
                    print(f"    Server: {server}")
        except requests.exceptions.SSLError:
            pass
        except Exception as e:
            if "Connection refused" in str(e) or "timed out" in str(e):
                pass  # Expected for some
            else:
                print(f"  [ERR] {path}: {type(e).__name__}")
    
    results[base] = host_results
    time.sleep(0.3)

# Summary
print("\n" + "=" * 70)
print("INTERESTING FINDINGS")
print("=" * 70)

total_interesting = 0
for base, findings in results.items():
    interesting = [f for f in findings if f["interesting"]]
    if interesting:
        print(f"\n{base}:")
        for f in interesting:
            total_interesting += 1
            redirect = ""
            if f["status"] in [301, 302, 307, 308]:
                redirect = ""
            print(f"  [{f['status']}] {f['url']} ({f['length']}b)")
            if f["body"]:
                print(f"    -> {f['body'][:120]}")

print(f"\nTotal interesting endpoints: {total_interesting}")

# Save
output_file = f"/home/bossjy/.hermes/cache/scratch/login_discovery_{int(time.time())}.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=2, default=str, ensure_ascii=False)
print(f"\n[*] Results saved to: {output_file}")
