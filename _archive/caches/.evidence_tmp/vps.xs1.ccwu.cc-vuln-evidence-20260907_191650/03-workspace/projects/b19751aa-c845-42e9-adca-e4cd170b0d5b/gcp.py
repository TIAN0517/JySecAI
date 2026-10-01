import requests, urllib3
urllib3.disable_warnings()
S = requests.Session(); S.verify=False
UA={"User-Agent":"Mozilla/5.0"}
G="http://35.234.50.28"

print("===== GCP EPCR :8000 main =====")
for p in ["/","/config","/js/publicConfig.js","/index.html","/login","/Users","/Roles","/Permissions","/api","/swagger","/debug"]:
    try:
        r=S.get(G+":8000"+p, timeout=10, headers=UA, allow_redirects=False)
        print(f"  [{r.status_code}] :8000{p} :: {r.headers.get('server','?')[:18]} {r.headers.get('content-type','')[:25]} {r.text[:90]!r}")
    except Exception as e:
        print(f"  [ERR] :8000{p} {e}")

print("\n===== GCP API :9000 (same as :4000) =====")
for p in ["/config","/js/publicConfig.js","/js/services.js","/Users","/Roles","/Permissions","/DispatchRecord","/socket.io/?EIO=3&transport=polling"]:
    try:
        r=S.get(G+":9000"+p, timeout=10, headers=UA, allow_redirects=False)
        print(f"  [{r.status_code}] :9000{p} :: {r.headers.get('content-type','')[:25]} {r.text[:90]!r}")
    except Exception as e:
        print(f"  [ERR] :9000{p} {e}")

print("\n===== GCP :30080 (nginx 403) =====")
for p in ["/","/index.html","/live","/stat.html"]:
    try:
        r=S.get(G+":30080"+p, timeout=10, headers=UA, allow_redirects=False)
        print(f"  [{r.status_code}] :30080{p} :: {r.text[:60]!r}")
    except Exception as e:
        print(f"  [ERR] :30080{p} {e}")

print("\n===== open-proxy / redirect probes on :8000 =====")
for p in ["/?url=http://evil.com","/?redirect=http://evil.com","/?next=http://evil.com","/redirect?url=http://evil.com","/?location=http://evil.com"]:
    try:
        r=S.get(G+":8000"+p, timeout=10, headers=UA, allow_redirects=False)
        print(f"  [{r.status_code}] {p} :: loc={r.headers.get('Location','?')!r} {r.text[:60]!r}")
    except Exception as e:
        print(f"  [ERR] {p} {e}")
print("done")
