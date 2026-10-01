import requests, urllib3
urllib3.disable_warnings()
S=requests.Session(); S.verify=False
UA={"User-Agent":"Mozilla/5.0"}
# Node.js / source / config / debug disclosure probes on AuthServer (staging + prod)
probes=["/","/config","/env","/package.json","/app.js","/debug","/_debugger","/api",
"/users","/node_modules","/node_modules/express/package.json","/.env","/server.js",
"/lib","/src","/config.js","/config.json","/secret","/api/config","/socket.io/?EIO=3&transport=polling",
"/favicon.ico","/robots.txt","/sitemap.xml","/.git/config","/.git/HEAD","/node_modules/.package-lock.json",
"/public","/static","/assets","/bower_components","/version"]
for base in ["http://35.234.50.28:3400","http://118.163.107.93:4004"]:
    print(f"\n########## {base} ##########")
    for p in probes:
        try:
            r=S.get(base+p,timeout=8,headers=UA)
            ct=r.headers.get("content-type","")
            if r.status_code not in (401,404) or len(r.text)>10:
                print(f"  [{r.status_code}] {p} len={len(r.text)} ct={ct} :: {r.text[:60]!r}")
        except Exception as ex: print(f"  [ERR] {p} {type(ex).__name__}")
print("done")
