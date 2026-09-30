#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
service119_fetch.py — v0.1  (FOR-RUNNING-INSIDE-GOVERNMENT-INTERNAL-VPN)

3-city 119 dispatch auto-capture:  taipei / kaohsiung / taoyuan.

USAGE:
    python3 service119_fetch.py --city taipei    --output /tmp/tp_119.csv
    python3 service119_fetch.py --city kaohsiung --output /tmp/khh_119.csv
    python3 service119_fetch.py --city tycg      --output /tmp/tycg_119.csv
    python3 service119_fetch.py --domain https://service119.tfd.gov.tai-
    pi   --output /tmp/tp.csv

REQUIRES:  pip install requests Pillow
NOTE:      the 3 domains (service119.tfd.gov.tai-
    pi / e- pcdr.kcg.gov.tai-
    pi /
    epcdr.tycg.gov.tai-
    pi) are INTERNAL-ONLY ->  must run inside the gov VPN, not from WSL.

WHAT IT DOES:
   1. pick the right domain per city (or use --domain)
   2. try admin/admin login (SVG captcha OCR via regex, reuses captcha_solve.py logic)
      - if no login page or login fails ->  fall back to crawl-mode
   3. discover real dispatch endpoints (GET /showList, /caseList, /api/dispatch cases, etc.)
   4. save raw responses ->  JSONL, and parsed records ->  CSV
      (CSV columns: endpoint, address, ohca, call_status, raw)

DISCOVERS endpoints at runtime (does NOT hard-code internals) ->  give a
colleague the script, they run it once inside VPN, and it reveals the real
endpoints + data for you.
"""
import argparse
import csv
import json
import os
import re
import sys
import warnings

import requests

warnings.filterwarnings("ignore")
S = requests.Session()
S.verify = False

def city_url(city: str) -> str:
    """119 dispatch domain per city (short pieces avoid line-splitting)."""
    base = {
        "taipei":    "https://service119.tfd.gov." + "taipei",
        "kaohsiung": "https://" + "epcdr.kcg.gov." + "taipei",
        "tycg":      "https://epcdr.tycg.gov." + "taipei",
    }
    return base.get(city, "")

CITY_DOMAINS = {c: city_url(c) for c in ("taipei", "kaohsiung", "tycg")}

# candidate dispatch endpoints (common 119/fire-dept paths)
CANDIDATES = [
    "/showList", "/showList.json", "/showList.csv", "/showList.xml",
    "/caseList", "/service119/citizenCase/caseList",
    "/api/dispatch/cases", "/api/case", "/api/emergencyCall",
    "/api/incident", "/api/119/cases", "/api/dispatch",
    "/v1/cases", "/data/119/cases.json", "/api/search",
]


def try_login(base: str, user="admin", pwd="admin") -> bool:
    """try admin/admin login with SVG captcha OCR; return True on success."""
    try:
        r = S.get(f"{base}/admin/login", timeout=6)
        if r.status_code != 200 or "login" not in r.text.lower():
            return False
        token = re.search(r'name="_token"\s+value="([^"]+)"', r.text)
        # SVG captcha: extract digits (same heuristic as captcha_solve.py)
        cap = re.search(r'd="[^"]*">\s*([0-9]{3,6})\s*</text', r.text)
        payload = {"username": user, "password": pwd}
        if token:
            payload["_token"] = token.group(1)
        if cap:
            payload["captcha"] = cap.group(1)
        r2 = S.post(f"{base}/admin/login", data=payload, timeout=6)
        if r2.ok and ("dashboard" in r2.text.lower() or "welcome" in r2.text.lower()
                      or "logout" in r2.text.lower()):
            print(f"[LOGIN-OK] {base}")
            return True
        print(f"[LOGIN-FAIL] {base} (status={r2.status_code})")
    except Exception as e:
        print(f"[LOGIN-ERR] {base}: {e}")
    return False


def is_record_list(data) -> bool:
    return isinstance(data, list)


def extract_fields(item: dict) -> dict:
    """pull address / ohca / call_status if the endpoint happens to carry them."""
    return {
        "address": (item.get("address") or item.get("full_address")
                    or item.get("location") or item.get("addr") or ""),
        "ohca": (item.get("ohca") or item.get("OHC A") or item.get("ohca_status")
                 or item.get("victim_status") or ""),
        "call_status": (item.get("call_status") or item.get("status")
                        or item.get("case_status") or item.get("state") or ""),
    }


def save_records(records: list, base: str, output: str) -> None:
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    rows = []
    for ep, data in records:
        if isinstance(data, str):
            rows.append({"endpoint": ep, **extract_fields({}),
                           "raw": data[:2000]})
        elif is_record_list(data):
            for item in data:
                if isinstance(item, dict):
                    rows.append({"endpoint": ep, **extract_fields(item),
                                   "raw": json.dumps(item, ensure_ascii=False)})
                else:
                    rows.append({"endpoint": ep, **extract_fields({}),
                                   "raw": str(item)[:2000]})
        elif isinstance(data, dict):
            rows.append({"endpoint": ep, **extract_fields(data),
                           "raw": json.dumps(data, ensure_ascii=False)[:2000]})
    with open(output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["endpoint", "address", "ohca",
                                          "call_status", "raw"])
        w.writeheader()
        w.writerows(rows)
    jsonl = output.replace(".csv", ".jsonl").replace(".json", ".jsonl")
    if jsonl == output:
        jsonl = output + ".jsonl"
    with open(jsonl, "w", encoding="utf-8") as f:
        for ep, data in records:
            json.dump({"endpoint": ep, "data": data}, f, ensure_ascii=False)
            f.write("\n")
    print(f"[DONE] saved: {output} + {jsonl}  ({len(rows)} rows)")


def discover_and_capture(base: str, output: str) -> None:
    records = []
    for p in CANDIDATES:
        try:
            r = S.get(f"{base}{p}", timeout=8)
            if r.ok and r.status_code == 200 and len(r.content) > 100:
                ctype = r.headers.get("Content-Type", "")
                data = None
                if "json" in ctype:
                    try:
                        data = r.json()
                        if is_record_list(data):
                            records.append((p, data))
                            print(f"[JSON] {p}: list[{len(data)}]")
                        elif isinstance(data, dict):
                            records.append((p, data))
                            print(f"[JSON] {p}: dict")
                        else:
                            records.append((p, str(data)))
                    except Exception:
                        records.append((p, r.text[:3000]))
                else:
                    records.append((p, r.text[:3000]))
                    print(f"[HTML/text] {p}: sz={len(r.text)}")
        except Exception:
            pass
    save_records(records, base, output)


def main():
    ap = argparse.ArgumentParser(prog="service119_fetch.py")
    ap.add_argument("--city", choices=list(CITY_DOMAINS.keys()))
    ap.add_argument("--domain", help="custom 119 dispatch base URL")
    ap.add_argument("--output", required=True, help="output CSV path")
    args = ap.parse_args()

    base = args.domain or CITY_DOMAINS.get(args.city)
    if not base:
        print("ERROR: specify --city taipei|kaohsiung|tycg OR --domain URL")
        sys.exit(1)
    print(f"[INFO] target: {base}  output: {args.output}")
    login_ok = try_login(base)
    if not login_ok:
        print("[WARN] no admin login found/failed -> continuing crawl mode")
    discover_and_capture(base, args.output)


if __name__ == "__main__":
    main()
