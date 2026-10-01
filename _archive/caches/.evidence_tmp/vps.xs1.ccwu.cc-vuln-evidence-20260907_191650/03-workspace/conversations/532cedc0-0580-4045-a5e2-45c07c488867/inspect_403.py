import requests, json, urllib3
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
r=s.get(BASE+"/captcha",timeout=12)
r=s.post(BASE+"/login",json={"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},timeout=12)
print("=== 403 完整响应 ===")
print("status:", r.status_code)
print("headers:")
for k,v in r.headers.items(): print(f"  {k}: {v}")
print("body:", r.text)
print("cookies:", dict(s.cookies))
# 看 500 完整
print("\n=== 500 完整响应 ===")
s2=requests.Session(); s2.verify=False; s2.headers.update({"User-Agent":"Mozilla/5.0"})
s2.get(BASE+"/captcha",timeout=12)
r2=s2.post(BASE+"/login",json={"username":"admin","password":"x","captcha":"1","domain":"AUTH_SERVER"},timeout=12)
print("status:", r2.status_code)
print("body:", r2.text[:300])
