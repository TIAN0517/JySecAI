#!/usr/bin/env python3
"""
Diagnostic: Find the exact FOFA API endpoint that works.
Try multiple URL formats with the key.
"""
import requests, json, base64, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

KEY = "dicl79nhrtolm07vqxk03fcqjyt4nvxu"
Q = "service119.tfd.gov.tw"
ENC = base64.b64encode(Q.encode()).decode()

s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

urls = [
    # api.fofa.info variants
    f"https://api.fofa.info/v1/search/all?key={KEY}&qbase64={ENC}",
    f"https://api.fofa.info/v1/search/all?qbase64={ENC}&key={KEY}",
    f"https://api.fofa.info/api/v1/search/all?key={KEY}&qbase64={ENC}",
    f"https://api.fofa.info/api/v1/search/all?qbase64={ENC}&key={KEY}",
    f"https://api.fofa.info/api/v1/search/all?qbase64={ENC}&key={KEY}&full=true",
    
    # fofoapi.com variants  
    f"https://fofoapi.com/api/v1/search/all?key={KEY}&qbase64={ENC}",
    f"https://fofoapi.com/api/v1/search/all?qbase64={ENC}&key={KEY}",
    f"https://fofoapi.com/v1/search/all?key={KEY}&qbase64={ENC}",
    f"https://fofoapi.com/v1/search/all?qbase64={ENC}&key={KEY}",
    f"https://fofoapi.com/?key={KEY}&qbase64={ENC}",
    
    # Try v2 endpoints
    f"https://api.fofa.info/v2/search/all?key={KEY}&qbase64={ENC}",
    f"https://api.fofa.info/v2/search/all?qbase64={ENC}&key={KEY}",
    
    # Try with token
    f"https://api.fofa.info/v1/search/all?token={KEY}&qbase64={ENC}",
    f"https://api.fofa.info/v1/search/all?qbase64={ENC}&token={KEY}",
    
    # Try fofoapi.com with token
    f"https://fofoapi.com/api/v1/search/all?qbase64={ENC}&token={KEY}",
    f"https://fofoapi.com/v1/search/all?qbase64={ENC}&token={KEY}",
]

for url in urls:
    try:
        r = s.get(url, timeout=15, verify=False, allow_redirects=False)
        status = r.status_code
        body = r.text[:200] if r.text else ""
        if status == 200:
            try:
                j = r.json()
                err = j.get("error", False)
                if err:
                    msg = j.get("errmsg", j.get("message", ""))
                    print(f"[{status}] ERR: {url.replace(KEY, KEY[:8]+'...')} -> {msg}")
                else:
                    results = j.get("results", [])
                    size = j.get("size", 0)
                    print(f"[{status}] OK:  {url.replace(KEY, KEY[:8]+'...')} -> {len(results)} results (size: {size})")
                    if results:
                        for res in results[:3]:
                            print(f"  -> {res[0] if res else '?'} | {res[1] if len(res)>1 else '?'}:{res[2] if len(res)>2 else '?'}")
            except:
                print(f"[{status}] HTML:  {url.replace(KEY, KEY[:8]+'...')} -> {body[:100]}")
        else:
            print(f"[{status}]     {url.replace(KEY, KEY[:8]+'...')} -> {body[:80]}")
    except Exception as e:
        print(f"ERR: {url.replace(KEY, KEY[:8]+'...')} -> {e}")
