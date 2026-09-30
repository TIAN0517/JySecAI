#!/usr/bin/env python3
"""
Carpet search - Phase 2: HTTP probing and directory brute force on open ports.
Focus: 107.173.248.139 ports 80, 443, 18888, 18999
"""
import subprocess
import requests
import json
import time
import re
import os

VERIFY = True
TARGET_IP = "107.173.248.139"
TARGET_PATH = "/dicl79nhrtolm07vqxk03fcqjyt4nvxu"

LOGIN_PATHS = [
    "login", "login.php", "login.jsp", "Login", "dologin",
    "auth", "auth/login", "api/auth", "api/login", "jwt/login",
    "admin/login", "admin/login.php", "admin/index.php",
    "user/login", "citizen/auth/genToken", "citizenCase/caseList",
    "genToken", "getUserToken", "fetchServerData",
    "swagger", "docs", "api-docs", "v1/auth", "v2/auth",
    "oauth/token", "oauth2/token", "api/token", "token",
    ".env", "config", "config.php", "config.json",
    "robots.txt", "favicon.ico",
    "api", "api/v1", "api/v2", "v1", "v2",
    "dashboard", "home", "index", "index.html",
    "portal", "services", "ws", "socket.io",
    "api/case", "api/patient", "api/ohca", "api/incident",
    "api/user", "api/ambulance", "api/discharge",
    "epcr", "mer", "mci", "monitor",
    "static", "assets", "public",
    "api/stream", "api/video", "api/event",
    "api/vitalsign", "vitalsign", "api/vitalsignvideo",
]

def http_probe(url, timeout=10):
    """Probe a URL and return status code, size, title."""
    try:
        r = requests.get(url, timeout=timeout, verify=VERIFY,
                        allow_redirects=False,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
        title = ""
        if r.headers.get("content-type", "").startswith("text/html"):
            t = re.search(r"<title>(.*?)</title>", r.text, re.DOTALL | re.IGNORECASE)
            if t:
                title = t.group(1).strip()
        server = r.headers.get("server", "")
        return {
            "status": r.status_code,
            "size": len(r.content),
            "title": title,
            "server": server,
            "headers": dict(r.headers),
            "body_preview": r.text[:500] if r.status_code == 200 else ""
        }
    except Exception as e:
        return {"error": str(e)}

def write_wordlist(paths, filepath="/tmp/carpet_wordlist.txt"):
    """Write wordlist to file for ffuf."""
    with open(filepath, "w") as f:
        for p in paths:
            f.write(p + "\n")
    return filepath

def ffuf_scan(base_url, wordlist_path, timeout=120):
    """Run ffuf directory brute force."""
    cmd = ["ffuf", "-w", wordlist_path, "-u", base_url + "/FUZZ",
           "-mc", "200,301,302,307,400,401,403,404,405,500,502,503",
           "-t", "50", "-s", "--timeout", "10", "-of", "json"]
    
    print(f"  [*] Running ffuf on {base_url}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        findings = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                try:
                    f = json.loads(line)
                    findings.append(f)
                except:
                    pass
        return findings
    except subprocess.TimeoutExpired:
        print(f"  [!] ffuf timed out on {base_url}")
        return []
    except Exception as e:
        print(f"  [!] ffuf error: {e}")
        return []

def main():
    results = {}
    open_ports = [80, 443, 18888, 18999]
    
    # ===== Phase 1: HTTP probing =====
    print("=" * 60)
    print("Phase 1: HTTP Probing on all open ports")
    print("=" * 60)
    
    for port in open_ports:
        for proto in ["http", "https"]:
            url = f"{proto}://{TARGET_IP}:{port}/"
            probe = http_probe(url)
            if "error" not in probe:
                key = f"{proto}://{TARGET_IP}:{port}"
                results[key] = probe
                print(f"  [{proto}] :{port} -> HTTP {probe['status']} | {probe['size']}b | Server: {probe['server']} | Title: {probe['title'][:60]}")
    
    # Probe the token path specifically on all ports
    print("\n  --- Token path probing ---")
    for port in open_ports:
        for proto in ["http", "https"]:
            url = f"{proto}://{TARGET_IP}:{port}{TARGET_PATH}"
            try:
                r = requests.get(url, timeout=10, verify=VERIFY, allow_redirects=False,
                               headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
                print(f"  [{proto}] :{port}{TARGET_PATH} -> HTTP {r.status_code} | {len(r.content)}b | Server: {r.headers.get('server','')}")
                # Try with different methods
                for method, method_name in [("POST", "POST"), ("HEAD", "HEAD")]:
                    r2 = requests.request(method, url, timeout=10, verify=VERIFY, allow_redirects=False,
                                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                    if r2.status_code != r.status_code:
                        print(f"  [{proto} {method}] :{port}{TARGET_PATH} -> HTTP {r2.status_code}")
            except Exception as e:
                print(f"  [{proto}] :{port}{TARGET_PATH} -> ERROR: {e}")
    
    # ===== Phase 2: Directory brute force =====
    print("\n" + "=" * 60)
    print("Phase 2: Directory Brute Force (ffuf)")
    print("=" * 60)
    
    wl_path = write_wordlist(LOGIN_PATHS)
    all_findings = {}
    
    for port in open_ports:
        for proto in ["http", "https"]:
            base = f"{proto}://{TARGET_IP}:{port}"
            # Check if port is accessible
            probe = http_probe(base, timeout=5)
            if "error" in probe:
                print(f"  [skip] {base} - not accessible")
                continue
            print(f"\n  [*] Scanning {base} (HTTP {probe['status']})")
            findings = ffuf_scan(base, wl_path, timeout=90)
            if findings:
                all_findings[base] = findings
                for f in findings:
                    # Skip the default 403/404 responses
                    if f.get("status") not in [403, 404]:
                        print(f"  [+] {base}{f.get('url', '')} -> HTTP {f.get('status')}")
                # Show all non-403 results
                non_403 = [f for f in findings if f.get("status") not in [403, 404]]
                if non_403:
                    print(f"  [!] Interesting findings (non-403/404):")
                    for f in non_403[:10]:
                        print(f"      {f.get('url')} -> HTTP {f.get('status')} | {f.get('length', 0)}b")
    
    results["dir_findings"] = all_findings
    
    # ===== Phase 3: Detailed probe of interesting endpoints =====
    print("\n" + "=" * 60)
    print("Phase 3: Detailed probe of key endpoints")
    print("=" * 60)
    
    key_endpoints = {}
    # From existing reports, these are important
    tpe_endpoints = [
        "https://service119.tfd.gov.tw/service119/citizenCase/caseList",
        "https://service119.tfd.gov.tw/service119/citizen/auth/genToken",
        "https://service119.tfd.gov.tw/service119/citizenCase/initUserCategory",
        "https://service119.tfd.gov.tw/service119/auth/fetchServerData",
        "https://service119.tfd.gov.tw/service119/api/getUserToken",
        "https://epcr.tpf.gov.tw:4000/config",
        "https://epcr.tpf.gov.tw:4001/events",
        "https://epcr.tpf.gov.tw:4004/",
        "https://epcr.tpf.gov.tw:4004/api/login",
        "https://epcr.tpf.gov.tw:4004/captcha",
        "https://epcr.tpf.gov.tw:4000/api/ohca",
    ]
    
    for ep in tpe_endpoints:
        probe = http_probe(ep)
        key_endpoints[ep] = probe
        status = probe.get("status", "ERR")
        size = probe.get("size", 0)
        title = probe.get("title", "")[:60]
        print(f"  {ep} -> HTTP {status} | {size}b | {title}")
    
    results["tpe_endpoints"] = key_endpoints
    
    # Save results
    output_file = f"/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/carpet_search_phase2_{int(time.time())}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str, ensure_ascii=False)
    print(f"\n[*] Results saved to: {output_file}")

if __name__ == "__main__":
    main()
