#!/usr/bin/env python3
"""Probe key subdomains for HTTP/HTTPS entry points."""
import ssl
import socket
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

# 重点子域：SSO 主站入口 + EPCR API
TARGETS = [
    ("t.epcr.tpf.gov.tw", [80, 443]),
    ("epcr.tpf.gov.tw", [80, 443, 4000, 4004]),
    ("mer2.tpf.gov.tw", [80, 443, 30080]),
    ("mer2voip.tpf.gov.tw", [80, 443, 30080]),
    ("t.mer2.tpf.gov.tw", [80, 443]),
    ("t.mer2voip.tpf.gov.tw", [80, 443]),
    ("119EpcrApi.tpf.gov.tw", [80, 443, 8080]),
    ("119epcrapi.tpf.gov.tw", [80, 443, 8080]),
    ("119api.tpf.gov.tw", [80, 443, 8080]),
    ("119Api.tpf.gov.tw", [80, 443, 8080]),
    ("119AppApi.tpf.gov.tw", [80, 443, 8080]),
    ("119appapi.tpf.gov.tw", [80, 443, 8080]),
    ("119appcaseapi.tpf.gov.tw", [80, 443, 8080]),
    ("119AppCaseApi.tpf.gov.tw", [80, 443, 8080]),
    ("119firecaseapi.tpf.gov.tw", [80, 443, 8080]),
    ("119FireCaseApi.tpf.gov.tw", [80, 443, 8080]),
    ("kemp.tpf.gov.tw", [80, 443]),
    ("kemp2.tpf.gov.tw", [80, 443]),
    ("www.tpf.gov.tw", [80, 443]),
    ("tpf.gov.tw", [80, 443]),
    ("epcrvoip.tpf.gov.tw", [80, 443]),
    ("sportal.emic.gov.tw", [80, 443]),
]

def probe(host, port, scheme):
    url = f"{scheme}://{host}:{port}/"
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8, context=ctx if scheme == "https" else None) as resp:
            code = resp.status
            loc = resp.headers.get("Location", "")
            server = resp.headers.get("Server", "")
            ct = resp.headers.get("Content-Type", "")
            body = resp.read(400)
            body_str = body[:400].decode("utf-8", errors="ignore")
            return (url, code, server, ct, loc, body_str)
    except urllib.error.HTTPError as e:
        return (url, e.code, e.headers.get("Server", ""), e.headers.get("Content-Type", ""), e.headers.get("Location", ""), str(e)[:200])
    except Exception as e:
        return (url, f"ERR: {type(e).__name__}", "", "", "", str(e)[:200])

def main():
    print(f"{'URL':<55} {'CODE':<6} {'SERVER':<25} {'CT':<35} LOC")
    print("-" * 180)
    tasks = []
    for host, ports in TARGETS:
        for port in ports:
            for scheme in ["http", "https"]:
                tasks.append((host, port, scheme))

    with ThreadPoolExecutor(max_workers=30) as ex:
        futures = {ex.submit(probe, h, p, s): (h, p, s) for h, p, s in tasks}
        for fut in as_completed(futures):
            try:
                res = fut.result()
                url, code, server, ct, loc, body = res
                if "ERR" not in str(code):
                    print(f"{url:<55} {str(code):<6} {server[:25]:<25} {ct[:35]:<35} {loc[:50]}")
                    if code in (200, 301, 302) and body:
                        print(f"  └─ BODY (first 200 chars): {body[:200]}")
            except Exception as e:
                pass

if __name__ == "__main__":
    main()
