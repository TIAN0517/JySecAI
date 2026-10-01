import urllib.request, urllib.error, json, ssl

BASE="https://ofa377.com.tw"
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

def get(path, headers=None, data=None, method=None):
    h=dict(UA)
    if headers: h.update(headers)
    body=None
    if data is not None:
        body=data.encode() if isinstance(data,str) else data
        h.setdefault("Content-Type","application/x-www-form-urlencoded")
    req=urllib.request.Request(BASE+path, data=body, headers=h, method=method)
    try:
        r=urllib.request.urlopen(req, timeout=20, context=ctx)
        return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return None, {"err":str(e)}, str(e).encode()

print("=== Rank Math namespace ===")
s,h,b=get("/wp-json/rankmath/v1")
print(s, b.decode(errors="ignore")[:2500])

print("\n=== wp-login.php 403 body (first 800) ===")
s,h,b=get("/wp-login.php")
print(s)
print(b[:1200].decode(errors="ignore"))

print("\n=== feed author/meta ===")
s,h,b=get("/feed/")
t=b.decode(errors="ignore")
import re
for m in re.findall(r'<dc:creator>(.*?)</dc:creator>', t)[:10]:
    print("creator:", m)
for m in re.findall(r'<link>(https://ofa377.com.tw/[a-z0-9-]+/?)</link>', t)[:20]:
    print("link:", m)
# search for usernames / email
for m in set(re.findall(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,})', t)):
    print("email:", m)
