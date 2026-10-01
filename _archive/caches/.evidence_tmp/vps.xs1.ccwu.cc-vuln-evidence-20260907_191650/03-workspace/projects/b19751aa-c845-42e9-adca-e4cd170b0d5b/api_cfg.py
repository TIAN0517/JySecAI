import urllib.request, urllib.error, json, ssl, re

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
def get(url, headers=None, timeout=25):
    h=dict(UA); 
    if headers: h.update(headers)
    req=urllib.request.Request(url, headers=h)
    try:
        r=urllib.request.urlopen(req, timeout=timeout, context=ctx)
        return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return None, {"err":str(e)}, str(e).encode()

for host in ["https://ofa377.net","https://www.ofa377.net","https://ofa377.com.tw"]:
    s,h,b=get(host+"/")
    txt=b.decode(errors="ignore") if b else ""
    print(f"\n##### {host}/ -> {s}  len={len(txt)}")
    # find script srcs and inline config
    for m in re.findall(r'<script[^>]*src="([^"]+)"', txt):
        print("  script:", m)
    # inline window config
    for m in re.findall(r'(window\.[A-Za-z_]+\s*=|__[A-Z_]+\s*|SITE[A-Z_]*|CONFIG|apiUrl|baseURL|VITE_)[^;<]{0,160}', txt):
        print("  cfg:", m[:180])
    # any json config
    for m in re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', txt, re.S):
        print("  jsoncfg:", m[:300])
