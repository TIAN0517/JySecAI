#!/usr/bin/env python3
"""Fetch all 4004 AuthServer JS files."""
import ssl
import urllib.request
import urllib.error

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

FILES = [
    "js/permissionlist.js",
    "js/app.js",
    "js/publicConfig.js",
    "js/authInterceptorConfig.config.js",
    "js/controllers.js",
    "js/services.js",
    "js/AuthService.js",
    "js/WholeBodyCtrl.js",
    "js/LoginCtrl.js",
    "js/LogoutCtrl.js",
    "js/Request2faCtrl.js",
    "js/PermissionCtrl.js",
    "js/RoleCtrl.js",
    "js/UserCtrl.js",
    "js/ChangePasswordCtrl.js",
    "js/Login2FACtrl.js",
]

for path in FILES:
    url = f"https://epcr.tpf.gov.tw:4004/{path}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            body = resp.read()
            fname = path.replace("/", "_")
            with open(f"/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/epcr_4004_{fname}", "wb") as f:
                f.write(body)
            print(f"OK  [{len(body):>6}B]  https://epcr.tpf.gov.tw:4004/{path}")
    except urllib.error.HTTPError as e:
        print(f"ERR {e.code}  https://epcr.tpf.gov.tw:4004/{path}")
    except Exception as e:
        print(f"ERR {type(e).__name__}  https://epcr.tpf.gov.tw:4004/{path}  {e}")