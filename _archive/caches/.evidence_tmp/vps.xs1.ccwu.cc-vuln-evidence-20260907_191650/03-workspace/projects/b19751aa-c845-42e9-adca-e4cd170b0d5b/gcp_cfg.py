import requests, urllib3, json
urllib3.disable_warnings()
S = requests.Session(); S.verify=False
UA={"User-Agent":"Mozilla/5.0"}

print("===== GCP :8000/config FULL =====")
r=S.get("http://35.234.50.28:8000/config", timeout=10, headers=UA)
print(r.text)

print("\n===== GCP :8000/js/publicConfig.js FULL =====")
r=S.get("http://35.234.50.28:8000/js/publicConfig.js", timeout=10, headers=UA)
print(r.text[:2000])

print("\n===== diff GCP config keys vs production =====")
try:
    g=json.loads(S.get("http://35.234.50.28:8000/config", timeout=10).text)
    p=json.loads(S.get("https://epcr.tpf.gov.tw:4000/config", timeout=10, verify=False).text)
    allkeys=sorted(set(g)|set(p))
    for k in allkeys:
        gv, pv = g.get(k,"<absent>"), p.get(k,"<absent>")
        mark = "" if gv==pv else "   <<< DIFFERS"
        print(f"  {k}:\n    GCP={gv!r}\n    PROD={pv!r}{mark}")
except Exception as e:
    print("diff err", e)
print("done")
