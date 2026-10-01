import requests,urllib3
urllib3.disable_warnings()
s=requests.Session(); s.verify=False
paths=["/config","/version","/js/app.js","/js/app.js.map","/js/AuthService.js",
"/.git/HEAD","/.git/config","/.git/index","/HEAD","/config/.env","/env",
"/.env.local","/config/env.js","/js/config.js","/js/publicConfig.js","/publicConfig.js",
"/api/config","/api/info","/api/health","/health","/status","/api/version","/swagger.json",
"/openapi.json","/api-docs","/docs","/favicon.ico","/robots.txt","/sitemap.xml",
"/js/publicConfig.js","/js/config.js","/config.json","/settings","/debug","/console"]
for h in ["4000","4004"]:
    print("==== port %s ===="%h)
    for p in paths:
        try:
            r=s.get("https://epcr.tpf.gov.tw:%s%s"%(h,p),timeout=12)
            flag="***" if (200<=r.status_code<300 and len(r.content)>0) else ""
            print("  %-26s %s %7dB %s"%(p,r.status_code,len(r.content),flag))
        except Exception as e:
            print("  %-26s ERR %s"%(p,str(e)[:35]))
