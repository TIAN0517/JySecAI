#!/usr/bin/env python3
"""
Probe epcr 4002 socket.io with proper Origin and HTTPS.
"""
import requests, urllib3, json, re, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BASE_HTTP = "http://epcr.tpf.gov.tw:4002"
BASE_HTTPS = "https://epcr.tpf.gov.tw:4002"


def attempt(label, url, headers=None, data=None):
    """Try handshake with given headers."""
    print(f"\n[{label}] GET {url}")
    print(f"  headers: {headers}")
    try:
        r = requests.get(url, headers=headers, timeout=8)
        print(f"  status={r.status_code} length={len(r.text)}")
        print(f"  body[:200]: {r.text[:200]}")
        m = re.search(r'"sid":"([^"]+)"', r.text)
        if m:
            sid = m.group(1)
            print(f"  *** HAND SHAKE OK sid={sid} ***")
            return sid
    except Exception as e:
        print(f"  ERR: {e}")
    return None


def main():
    # Step 0: Warm up - GET /config or / to get cookies
    print("===== Warmup GETs =====")
    for url in [BASE_HTTP, BASE_HTTP + "/", BASE_HTTP + "/config", BASE_HTTPS, BASE_HTTPS + "/"]:
        print(f"  GET {url}")
        try:
            r = requests.get(url, timeout=8, verify=False, allow_redirects=False)
            print(f"    status={r.status_code} length={len(r.text)} cookies={dict(r.cookies)}")
        except Exception as e:
            print(f"    ERR: {e}")

    # Step 1: Try with Origin header
    print("\n===== Step 1: with Origin =====")
    headers = {"Origin": "https://epcr.tpf.gov.tw:4002",
               "Referer": "https://epcr.tpf.gov.tw:4002/",
               "User-Agent": "Mozilla/5.0"}
    sid = attempt("Origin", BASE_HTTP + "/socket.io/?EIO=4&transport=polling", headers)

    if not sid:
        # Step 2: HTTPS protocol
        sid = attempt("HTTPS+Origin", BASE_HTTPS + "/socket.io/?EIO=4&transport=polling", headers)

    if not sid:
        # Step 3: Try with session cookie
        print("\n===== Step 3: Get connect.sid first =====")
        s = requests.Session()
        for url in [BASE_HTTP + "/config", BASE_HTTP + "/version", BASE_HTTP + "/"]:
            try:
                r = s.get(url, timeout=5, verify=False)
                print(f"  {url} -> cookies={dict(s.cookies)}")
            except Exception as e:
                print(f"  {url} ERR {e}")
        # Now try socket.io with cookie
        print("\n  Now socket.io with session cookie:")
        try:
            r = s.get(BASE_HTTP + "/socket.io/?EIO=4&transport=polling", headers=headers, timeout=8)
            print(f"  status={r.status_code} length={len(r.text)}")
            print(f"  body[:300]: {r.text[:300]}")
            sid = re.search(r'"sid":"([^"]+)"', r.text)
            if sid:
                print(f"  *** SID={sid.group(1)} ***")
                sid = sid.group(1)
        except Exception as e:
            print(f"  ERR: {e}")


if __name__ == "__main__":
    main()