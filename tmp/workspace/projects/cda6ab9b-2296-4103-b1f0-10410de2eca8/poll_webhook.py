#!/usr/bin/env python3
"""
Poll webhook.site for received requests from planted XSS payloads.
Run in background; print every 5 minutes.
"""
import requests, urllib3, json, time, sys
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

UUID = "9938583b-2e29-4de9-8231-ac50b3e44016"
TOKEN = UUID  # webhook.site uses UUID as token for the API

POLL_INTERVAL = 300  # 5 minutes
OUT_LOG = "/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/out_webhook.log"


def fetch_requests():
    url = f"https://webhook.site/token/{TOKEN}/requests?sorting=newest"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        return {"err": str(e)}


def main():
    last_total = -1
    seen_ids = set()
    print(f"[poll] start: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    while True:
        data = fetch_requests()
        if data is None:
            print(f"[poll] {time.strftime('%H:%M:%S', time.gmtime())} HTTP err")
        elif "err" in data:
            print(f"[poll] {time.strftime('%H:%M:%S', time.gmtime())} fetch err: {data['err']}")
        else:
            total = data.get("total", 0)
            if total != last_total:
                print(f"[poll] {time.strftime('%H:%M:%S', time.gmtime())} total={total}")
                # dump new requests
                for req in data.get("data", []):
                    rid = req.get("uuid", "")
                    if rid in seen_ids:
                        continue
                    seen_ids.add(rid)
                    print(f"  *** NEW REQUEST uuid={rid[:12]}...")
                    print(f"      method={req.get('method')} url={req.get('url')}")
                    print(f"      ip={req.get('ip')} ua={req.get('user_agent', '')[:80]}")
                    print(f"      time={req.get('created_at')}")
                last_total = total
            else:
                print(f"[poll] {time.strftime('%H:%M:%S', time.gmtime())} total={total} (no change)")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("[poll] interrupted")