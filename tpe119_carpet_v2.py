#!/usr/bin/env python3
"""
Carpet search - Phase 2b: Fixed HTTP probing with proper protocol handling.
Also probe HTTPS with verify=False for self-signed certs.
And re-test service119 with POST requests.
"""
import subprocess
import requests
import json
import time
import re
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET_IP = "107.173.248.139"
TARGET_PATH = "/dicl79nhrtolm07vqxk03fcqjyt4nvxu"
OPEN_PORTS = [80, 443, 18888, 18999]

def http_probe(url, timeout=10, method="GET", data=None, allow_redirects=False):
    """Probe a URL and return status code, size, title."""
    try:
        if method == "GET":
            r = requests.get(url, timeout=timeout, verify=False,
                            allow_redirects=allow_redirects,
                            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
        elif method == "POST":
            r = requests.post(url, timeout=timeout, verify=False,
                             allow_redirects=allow_redirects,
                             headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                      "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
                                      "Content-Type": "application/x-www-form-urlencoded"},
                             data=data)
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
            "body_preview": r.text[:1000] if r.status_code in [200, 301, 302, 400, 401, 403, 404, 500] else ""
        }
    except Exception as e:
        return {"error": str(e)}

def write_wordlist(paths, filepath="/tmp/carpet_wordlist.txt"):
    with open(filepath, "w") as f:
        for p in paths:
            f.write(p + "\n")
    return filepath

def ffuf_scan(base_url, wordlist_path, timeout=120):
    """Run ffuf directory brute force."""
    wl_path = write_wordlist(["login", "admin", "api", "config", "health", "status", "auth", "docs", "swagger", "v1", "v2", "portal", "dashboard", "ws", "socket.io"])
    cmd = ["ffuf", "-w", wl_path, "-u", base_url + "/FUZZ",
           "-mc", "200,301,302,307,400,401,403,404,405,500,502,503",
           "-t", "50", "-s", "--timeout", "10", "-of", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        findings = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                try:
                    findings.append(json.loads(line))
                except:
                    pass
        return findings
    except subprocess.TimeoutExpired:
        return []
    except Exception as e:
        print(f"  ffuf error: {e}")
        return []

def main():
    results = {}
    
    # ===== Phase 1: Proper HTTP probing with correct protocols =====
    print("=" * 70)
    print("Phase 1: HTTP/HTTPS Probing (correct protocols)")
    print("=" * 70)
    
    for port in OPEN_PORTS:
        # Determine protocol
        if port == 443:
            protos = ["https"]
        elif port == 80:
            protos = ["http"]
        else:
            protos = ["http", "https"]
        
        for proto in protos:
            url = f"{proto}://{TARGET_IP}:{port}/"
            probe = http_probe(url, timeout=10)
            key = f"{proto}://{TARGET_IP}:{port}"
            results[key] = probe
            if "error" in probe:
                print(f"  [{proto}] :{port}/ -> ERROR: {probe['error'][:80]}")
            else:
                print(f"  [{proto}] :{port}/ -> HTTP {probe['status']} | {probe['size']}b | Server: {probe['server']} | Title: {probe['title'][:50]}")
                if probe.get("body_preview"):
                    bp = probe["body_preview"].replace("\n", " ").strip()
                    print(f"    Body: {bp[:200]}")
    
    # ===== Phase 2: Token path probing with all methods =====
    print("\n" + "=" * 70)
    print("Phase 2: Token path probing")
    print("=" * 70)
    
    for port in OPEN_PORTS:
        for proto in ["http", "https"]:
            url = f"{proto}://{TARGET_IP}:{port}{TARGET_PATH}"
            # GET
            probe = http_probe(url, timeout=10, method="GET", allow_redirects=False)
            status_str = f"HTTP {probe.get('status','ERR')}" if "error" not in probe else f"ERR"
            print(f"  [{proto} GET] :{port}{TARGET_PATH} -> {status_str} | {probe.get('size',0)}b")
            if "error" not in probe and probe.get("body_preview"):
                print(f"    Body: {probe['body_preview'].replace(chr(10), ' ').strip()[:200]}")
            
            # POST
            probe = http_probe(url, timeout=10, method="POST", data="t=1234567890", allow_redirects=False)
            status_str = f"HTTP {probe.get('status','ERR')}" if "error" not in probe else f"ERR"
            print(f"  [{proto} POST] :{port}{TARGET_PATH} -> {status_str} | {probe.get('size',0)}b")
            
            # HEAD
            try:
                r = requests.head(url, timeout=10, verify=False, allow_redirects=False,
                                headers={"User-Agent": "Mozilla/5.0"})
                print(f"  [{proto} HEAD] :{port}{TARGET_PATH} -> HTTP {r.status_code} | {len(r.content)}b")
            except Exception as e:
                print(f"  [{proto} HEAD] :{port}{TARGET_PATH} -> ERR")
    
    # ===== Phase 3: Directory brute force on accessible ports =====
    print("\n" + "=" * 70)
    print("Phase 3: Directory Brute Force (ffuf)")
    print("=" * 70)
    
    # Port 80 - likely nginx default, try anyway
    for port in [80, 18999]:
        base = f"http://{TARGET_IP}:{port}"
        probe = http_probe(base, timeout=5)
        if "error" not in probe and probe["status"] in [200, 403, 502]:
            print(f"\n  [*] Scanning {base}")
            findings = ffuf_scan(base, "/tmp/carpet_wordlist.txt")
            if findings:
                for f in findings:
                    status = f.get("status")
                    path = f.get("url", "")
                    size = f.get("length", 0)
                    if status not in [403, 404]:
                        print(f"  [+] {path} -> HTTP {status} | {size}b")
    
    # Port 443 with HTTPS
    base = f"https://{TARGET_IP}:443"
    probe = http_probe(base, timeout=10)
    if "error" not in probe and probe["status"] in [200, 302, 403]:
        print(f"\n  [*] Scanning {base}")
        # Try ffuf on HTTPS
        wl = write_wordlist(["login", "admin", "api", "config", "health", "status", "auth", "docs", "portal", "dashboard"])
        cmd = ["ffuf", "-w", wl, "-u", base + "/FUZZ", "-mc", "200,301,302,400,401,403,404,500", "-t", "50", "-s", "--timeout", "10", "-of", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        findings = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                try:
                    findings.append(json.loads(line))
                except:
                    pass
        if findings:
            for f in findings:
                status = f.get("status")
                path = f.get("url", "")
                if status not in [403, 404]:
                    print(f"  [+] {path} -> HTTP {status} | {f.get('length', 0)}b")
    
    # ===== Phase 4: Re-probe service119 endpoints with POST =====
    print("\n" + "=" * 70)
    print("Phase 4: service119.tfd.gov.tw endpoint re-test (POST)")
    print("=" * 70)
    
    s119_endpoints = {
        "https://service119.tfd.gov.tw/service119/citizenCase/caseList": "t=1234567890",
        "https://service119.tfd.gov.tw/service119/citizen/auth/genToken": "",
        "https://service119.tfd.gov.tw/service119/citizenCase/initUserCategory": "",
        "https://service119.tfd.gov.tw/service119/auth/fetchServerData": "",
    }
    
    for ep, data in s119_endpoints.items():
        # GET first
        probe = http_probe(ep, timeout=15, method="GET")
        print(f"  GET  {ep} -> HTTP {probe.get('status','ERR')} | {probe.get('size',0)}b")
        if probe.get("body_preview"):
            print(f"    Body: {probe['body_preview'].replace(chr(10), ' ').strip()[:200]}")
        
        # POST with timestamp
        if data:
            probe = http_probe(ep, timeout=15, method="POST", data=data)
            print(f"  POST {ep} -> HTTP {probe.get('status','ERR')} | {probe.get('size',0)}b")
            if probe.get("body_preview"):
                print(f"    Body: {probe['body_preview'].replace(chr(10), ' ').strip()[:200]}")
    
    # Also try without proxy (the old reports used a proxy at 202.160.76.155)
    print("\n  --- Testing service119 with proxy (202.160.76.155:11084) ---")
    proxies = {"https": "socks5h://202.160.76.155:11084", "http": "socks5h://202.160.76.155:11084"}
    for ep, data in s119_endpoints.items():
        try:
            r = requests.post(ep, data=data or "t=1234567890", timeout=15, verify=False, allow_redirects=False,
                            proxies=proxies,
                            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                                     "Content-Type": "application/x-www-form-urlencoded"})
            print(f"  POST (proxy) {ep} -> HTTP {r.status_code} | {len(r.content)}b")
            if r.status_code == 200:
                print(f"    Body: {r.text[:300]}")
        except Exception as e:
            print(f"  POST (proxy) {ep} -> ERR: {e}")
    
    # Also try direct HTTPS to EPCR ports
    print("\n  --- EPCR port probing ---")
    epcr_ports = [4000, 4001, 4002, 4003, 4004, 4005, 4006, 4007, 4008]
    for port in epcr_ports:
        url = f"https://epcr.tpf.gov.tw:{port}/"
        probe = http_probe(url, timeout=10)
        if "error" not in probe:
            print(f"  :{port} -> HTTP {probe['status']} | {probe['size']}b | {probe.get('title','')[:40]}")
        else:
            print(f"  :{port} -> ERR: {probe['error'][:60]}")
    
    # Save results
    output_file = f"/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/carpet_scan_v2_{int(time.time())}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str, ensure_ascii=False)
    print(f"\n[*] Results saved to: {output_file}")

if __name__ == "__main__":
    main()
