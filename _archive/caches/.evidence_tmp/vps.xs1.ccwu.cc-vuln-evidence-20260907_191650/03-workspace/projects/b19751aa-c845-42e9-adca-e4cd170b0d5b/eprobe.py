import requests, urllib3
urllib3.disable_warnings()
H = {"User-Agent":"Mozilla/5.0 (X11; Linux x86_64)"}
S = requests.Session(); S.verify=False

# candidate API endpoints for EPCR data server + hospital server
eps = [
 "/", "/api","/api/","/api/case","/api/cases","/case","/cases","/caselist","/caseList",
 "/patient","/patients","/dispatch","/record","/records","/vitalsign","/vitalSign",
 "/video","/audio","/image","/mci","/mcilist","/report","/reports","/user","/users",
 "/admin","/login","/logout","/token","/auth","/api/user","/api/login",
 "/v1/case","/v2/case","/service","/service/case","/caserecord","/caseRecord",
 "/getFile","/videoData/getFile/","/imageData/getFile/","/voiceData/getFile/",
 "/getCase","/getRecord","/query","/search","/export","/print","/bulletin","/device",
 "/branch","/hospital","/doctor","/emt","/ambulance","/supplies","/config","/stat",
 "/socket.io/","/socket.io/?EIO=3&transport=polling",
]
for base in ["https://epcr.tpf.gov.tw:4000","https://epcr.tpf.gov.tw:4002"]:
    print("\n########", base, "########")
    seen=set()
    for p in eps:
        try:
            r = S.get(base+p, timeout=12, headers=H, allow_redirects=False)
            key=(r.status_code, r.headers.get("content-type","")[:20])
            sig = (r.status_code, len(r.content))
            # print non-404/401/403 OR json
            if r.status_code in (200,201,301,302,307,500,400,405,409) :
                print(f"{r.status_code:3} len={len(r.content):6} {r.headers.get('content-type','')[:26]:26} {p}  :: {r.text[:50].strip()!r}")
        except Exception:
            pass
print("done")
