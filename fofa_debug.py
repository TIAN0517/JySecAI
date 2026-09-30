#!/usr/bin/env python3
"""
Phase 5: Subdomain carpet search - simplified to use only the working endpoint.
From the earlier test, BOTH api.fofa.info AND fofoapi.com worked with key param.
The error is likely rate limiting or the full=true param. Let's debug.
"""
import requests, json, base64, time, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FOFA_KEY = "dicl79nhrtolm07vqxk03fcqjyt4nvxu"

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})

Q = "service119.tfd.gov.tw"
ENC = base64.b64encode(Q.encode()).decode()

# Try different URL formats
urls = [
    f"https://api.fofa.info/v1/search/all?key={FOFA_KEY}&qbase64={ENC}",
    f"https://fofoapi.com/api/v1/search/all?key={FOFA_KEY}&qbase64={ENC}",
    f"https://api.fofa.info/v1/search/all?key={FOFA_KEY}&qbase64={ENC}&full=true",
    f"https://fofoapi.com/api/v1/search/all?key={FOFA_KEY}&qbase64={ENC}&full=true",
]

for url in urls:
    try:
        r = s.get(url, timeout=15, verify=False)
        print(f"[{r.status_code}] {url[:80]}...")
        try:
            j = r.json()
            if j.get("error"):
                print(f"  Error: {j.get('errmsg', j.get('message', ''))}")
            else:
                results = j.get("results", [])
                print(f"  Results: {len(results)} (size: {j.get('size', '?')})")
                if results:
                    for res in results[:3]:
                        print(f"  -> {res}")
        except:
            print(f"  Non-JSON: {r.text[:200]}")
    except Exception as e:
        print(f"  Exception: {e}")
    print()
    time.sleep(1)
