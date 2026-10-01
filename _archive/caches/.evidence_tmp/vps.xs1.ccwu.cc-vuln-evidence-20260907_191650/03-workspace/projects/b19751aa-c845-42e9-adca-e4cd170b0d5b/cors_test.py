import requests, urllib3
urllib3.disable_warnings()
S = requests.Session(); S.verify=False
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64)"}

print("=========== CORS TEST ===========")
for base in ["https://epcr.tpf.gov.tw:4000","https://epcr.tpf.gov.tw:4002","https://epcr.tpf.gov.tw:4004"]:
    for path in ["/config","/Users","/api/case","/"]:
        for origin in ["https://evil.com","https://epcr.tpf.gov.tw:4004","http://localhost","null"]:
            h=dict(UA); h["Origin"]=origin
            try:
                r=S.get(base+path, timeout=10, headers=h, allow_redirects=False)
                acao=r.headers.get("Access-Control-Allow-Origin")
                acac=r.headers.get("Access-Control-Allow-Credentials")
                if acao or acac:
                    print(f"{base}{path} origin={origin:30} => ACO={acao} ACC={acac}")
            except Exception as e:
                pass
    # preflight
    h={"Origin":"https://evil.com","Access-Control-Request-Method":"POST","Access-Control-Request-Headers":"authorization,content-type"}
    try:
        r=S.options(base+"/Users", timeout=10, headers=h, allow_redirects=False)
        print(f"  PREFLIGHT {base}/Users => {r.status_code} ACO={r.headers.get('Access-Control-Allow-Origin')} AM={r.headers.get('Access-Control-Allow-Methods')} AH={r.headers.get('Access-Control-Allow-Headers')}")
    except Exception: pass
print("done cors")
