#!/usr/bin/env python3
"""Fetch all JS files from EPCR 4002 HospitalServer."""
import ssl
import urllib.request
import urllib.error
import os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE = "https://epcr.tpf.gov.tw:4002"
OUT_DIR = "/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8"

JS_PATHS = [
    "js/permissionlist.js",
    "js/app.js",
    "js/publicConfig.js",
    "js/controllers.js",
    "js/services.js",
    "js/SocketIoService.js",
    "js/AuthService.js",
    "js/LoginCtrl.js",
    "js/LogoutCtrl.js",
    "js/HospitalCtrl.js",
    "js/HospitalCapabilityCtrl.js",
    "js/BackTrackingEditorCtrl.js",
    "js/CaseListCtrl.js",
    "js/CaseDetailCtrl.js",
    "js/PcrQuestionService.js",
    "js/HospitalCapabilityListCtrl.js",
    "js/HospitalCapabilityListForHealthCtrl.js",
    "js/HospitalAbilityCtrl.js",
    "js/HospitalChiefComplaintCtrl.js",
    "js/DispatchCtrl.js",
    "stat/epcr106/js/StatCommon.js",
    "stat/epcr106/js/StatApp.js",
    "stat/epcr106/js/StatBaseCtrl.js",
    "stat/epcr106/js/Stat01Ctrl.js",
    "stat/epcr106/js/Stat02Ctrl.js",
    "stat/epcr106/js/Stat03Ctrl.js",
]

for path in JS_PATHS:
    url = BASE + "/" + path
    safe = path.replace("/", "_")
    out = os.path.join(OUT_DIR, f"epcr_4002_{safe}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            body = resp.read()
            content_type = resp.headers.get("Content-Type", "")
            print(f"[{resp.status}] {path:<55s} {len(body):>7}B  CT={content_type}")
            with open(out, "wb") as f:
                f.write(body)
    except urllib.error.HTTPError as e:
        body = e.read()
        print(f"[{e.code}] {path:<55s} {len(body):>7}B")
    except Exception as e:
        print(f"[ERR] {path:<55s} {type(e).__name__}: {e}")
