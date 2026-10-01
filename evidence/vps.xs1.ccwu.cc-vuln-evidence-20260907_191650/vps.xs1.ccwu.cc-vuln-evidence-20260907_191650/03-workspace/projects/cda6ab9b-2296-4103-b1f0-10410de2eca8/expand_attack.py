#!/usr/bin/env python3
"""
Use admin2 JWT (cross-service shared secret) to test ALL backend services
on EPCR GCP and main domain
"""
import json
import urllib.request
import urllib.error

with open("/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/tokens.json") as f:
    JWT = json.load(f)['jwt']

# EPCR backend services - test admin2 JWT cross-service reachability
endpoints = [
    # 3400 - main authServer
    "http://35.234.50.28:3400/refreshToken",
    "http://35.234.50.28:3400/users",
    "http://35.234.50.28:3400/users/1",
    "http://35.234.50.28:3400/Permissions",
    "http://35.234.50.28:3400/Roles",
    # 3800 - mciServer (大傷系統)
    "http://35.234.50.28:3800/MciTypes",
    "http://35.234.50.28:3800/MciCaseRecords",
    # 3200 - HospitalServer
    "http://35.234.50.28:3200/api",
    "http://35.234.50.28:3200/config",
    # 3001 - statUrl
    "http://35.234.50.28:3001/config",
    "http://35.234.50.28:3001/js/permissionlist.js",
    # 8000 - EPCRServer
    "http://35.234.50.28:8000/config",
    "http://35.234.50.28:8000/version/",
    # 4001 - vitalSignVideo events (NOAUTH)
    "http://35.234.50.28:4001/events",
    # 4008 - mciServer collections (NOAUTH)
    "http://35.234.50.28:4008/MciTypes",
    "http://35.234.50.28:4008/MciCaseRecords",
    # 4000 - main domain
    "https://epcr.tpf.gov.tw:4000/config",
    "https://epcr.tpf.gov.tw:3400/users/1",
    "https://epcr.tpf.gov.tw:3800/MciTypes",
    # 118.163.107.93 mirror (if still reachable)
    "http://118.163.107.93:3400/users/1",
    "http://118.163.107.93:3800/MciTypes",
]

for url in endpoints:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {JWT}"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            body = r.read().decode('utf-8', errors='replace')
            print(f"[+] {url:60s} {r.status} {len(body):6d}B")
            # Show snippet for first occurrence of "permission" or "MciType"
            if "permission" in body.lower() or "MciType" in body or "config" in url:
                print(f"    snippet: {body[:300]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f"[-] {url:60s} {e.code} {len(body):6d}B  {body[:100]}")
    except Exception as e:
        print(f"[!] {url:60s} ERR: {e}")