import urllib.request, urllib.error, json, ssl, time, random, string

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
def post(path, data, base="https://ofa377.net/api", ct="application/json", headers=None):
    h={"User-Agent":UA["User-Agent"],"Content-Type":ct,"Origin":"https://ofa377.net","Referer":"https://ofa377.net/"}
    if headers: h.update(headers)
    body=json.dumps(data).encode()
    req=urllib.request.Request(base+path, data=body, headers=h, method="POST")
    try:
        r=urllib.request.urlopen(req, timeout=25, context=ctx)
        return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return None, {"err":str(e)}, str(e).encode()

def rnd(n=8): return ''.join(random.choices(string.ascii_lowercase+string.digits,k=n))

print("=== 1. register empty ===")
s,h,b=post("/v2/register/", {})
print(s, b[:400].decode(errors="ignore"))

print("\n=== 2. register minimal (username+password) ===")
u1="cyb"+rnd()
s,h,b=post("/v2/register/", {"username":u1,"password":"Passw0rd!"+rnd(4)})
print(s, b[:400].decode(errors="ignore"))

print("\n=== 3. register full fields ===")
u2="cyb"+rnd()
s,h,b=post("/v2/register/", {
  "bank_account":"12345678901234","bank_code":"BOCHK","bank_currency":"TWD","bank_name":"Cyber Sec",
  "email":"cyb"+rnd()+"@proton.me","line":"cyb"+rnd(),"name":"Cyber Test",
  "password":"Passw0rd!xyz123","phone_number":"+886912345678",
  "refer_code":"","username":u2,"verify_code":"123456"})
print(s, b[:500].decode(errors="ignore"))
print("  >> username:", u2)

print("\n=== 4. login fake creds (response shape) ===")
s,h,b=post("/v1/login", {"username":"cybnonexist999","password":"wrongpass123","device_id":"test-device-001"})
print(s, b[:400].decode(errors="ignore"))

print("\n=== 5. login for u2 (just registered) ===")
s,h,b=post("/v1/login", {"username":u2,"password":"Passw0rd!xyz123","device_id":"test-device-002"})
print(s, b[:500].decode(errors="ignore"))
