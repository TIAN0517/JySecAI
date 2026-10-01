import requests, json, urllib3
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})

print("=== 其他公开端点探测 (无需token) ===")
paths=["/health","/healthz","/status","/ping","/metrics","/debug","/debug/vars","/version",
  "/info","/api/version","/config","/env","/robots.txt","/favicon.ico","/.well-known/openid-configuration",
  "/oauth","/oauth/authorize","/.env","/swagger","/api-docs","/graphql","/ws","/socket.io"]
for p in paths:
    try:
        r=s.get(BASE+p,timeout=6)
        ct=r.headers.get("Content-Type","")
        if r.status_code!=401 or "html" not in ct:
            print(f"  GET {p:32s} -> {r.status_code} {ct[:25]} | {r.text[:40]}")
    except Exception as e:
        print(f"  GET {p:32s} -> ERR {repr(e)[:30]}")
print("DONE")
