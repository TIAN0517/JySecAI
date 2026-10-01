#!/usr/bin/env python3
# Simple path enumeration tool
import requests, sys, time
from urllib.parse import urljoin

def scan_paths(base_url, paths, delay=0.1):
    found = []
    for path in paths:
        url = urljoin(base_url + '/', path.lstrip('/'))
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code < 403:
                print(f"[+] {url} -> {resp.status_code}")
                found.append((url, resp.status_code))
        except:
            pass
        time.sleep(delay)
    return found

if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "https://apib63.bf1788.com"
    paths = ["/api", "/admin", "/debug", "/v1", "/boxApi.php", "/cmd"]
    scan_paths(base, paths)
