#!/usr/bin/env python3
"""Deep probe kemp.tpf.gov.tw:80 (Apache/2.4.52 DrApp 后台)."""
import ssl
import json
import urllib.request
import urllib.error

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE = "http://kemp.tpf.gov.tw"

# Common Laravel / admin paths
PATHS = [
    "/", "/index.php", "/login", "/admin", "/admin/login", "/admin.php",
    "/api", "/api/", "/api/login", "/api/users", "/api/v1",
    "/api/v1/users", "/api/v1/login",
    "/swagger", "/api-docs", "/docs",
    "/health", "/healthcheck", "/version",
    "/info", "/phpinfo", "/phpinfo.php",
    "/.env", "/env", "/.git", "/.git/config",
    "/robots.txt", "/sitemap.xml",
    "/v1/login", "/v2/login",
    "/user", "/users", "/users/login",
    "/dashboard", "/home", "/panel",
    "/manager", "/manage", "/system",
    "/console", "/artisan", "/tinker",
    "/vendor", "/vendor/laravel/framework",
    "/storage", "/storage/logs",
    "/storage/logs/laravel.log", "/storage/framework/sessions",
    "/debug", "/debugbar",
    "/public", "/index.html", "/index.htm",
    "/administrator",
    "/Login.aspx", "/default.aspx",
    "/_debug", "/_profiler",
    "/graphql", "/graphiql",
    "/graphql/v1",
    "/api/auth", "/api/auth/login", "/api/authenticate",
    "/api/token", "/auth/token",
    "/api/getUserInfo", "/api/getUser",
    "/api/Patient", "/api/Patient/1",
    "/api/Patient/2",
    "/cgi-bin", "/cgi-bin/",
    "/manage/login", "/console/login",
    "/backend", "/admin/login.php",
    "/web.config", "/config.php", "/config.yml", "/config.json",
    "/drapp", "/drapp/", "/drapp/login",
    "/api/system", "/api/system/version",
    "/.htaccess", "/.htpasswd",
    "/html", "/app",
    "/static", "/assets", "/css", "/js",
    "/img", "/images",
    "/favicon.ico",
    "/medias", "/uploads",
    "/Scripts", "/script",
    "/ajax", "/xajax",
    "/Home", "/Main",
    "/test.php", "/info.php", "/test.html",
    "/api-docs/swagger.json", "/swagger.json", "/openapi.json",
    "/fhir", "/fhir/metadata", "/fhir/Patient",
    "/hl7", "/hl7/ADT",
]

import re
import http.client

def probe_path(path):
    url = BASE + path
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            body_bytes = resp.read()
            ct = resp.headers.get("Content-Type", "")
            cl = resp.headers.get("Content-Length", "?")
            print(f"[{resp.status}] {path:<40s}  CT={ct[:50]:<50s}  CL={cl}")
            return resp.status, body_bytes, dict(resp.headers)
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        ct = e.headers.get("Content-Type", "")
        cl = e.headers.get("Content-Length", "?")
        body_text = body_bytes.decode("utf-8", "replace")[:200]
        print(f"[{e.code}] {path:<40s}  CT={ct[:50]:<50s}  CL={cl}  body={body_text!r}")
        return e.code, body_bytes, dict(e.headers)
    except Exception as e:
        print(f"[ERR] {path:<40s}  {type(e).__name__}: {e}")
        return None, None, None

print("=" * 100)
print(f"KEMP DrApp 后台探测 - {BASE}")
print("=" * 100)
for p in PATHS:
    probe_path(p)
