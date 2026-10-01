import urllib.request, urllib.error, json, ssl, re

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0 Safari/537.36","Accept":"*/*"}
def get(url, headers=None):
    h=dict(UA)
    if headers: h.update(headers)
    req=urllib.request.Request(url, headers=h)
    try:
        r=urllib.request.urlopen(req, timeout=20, context=ctx)
        return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, str(e).encode()

base="https://ofa77.shop"
s,eb=get(base+"/_nonexistent_xyz123")
open("ofa77_errdump.html","wb").write(eb)
txt=eb.decode(errors="ignore")
print("=== ERROR DUMP analysis (len %d) ==="%len(txt))
# strip html tags for text
plain=re.sub(r'<[^>]+>','',txt)
# find file paths
paths=sorted(set(re.findall(r'/www/wwwroot/[A-Za-z0-9_./\-]+', plain)))
print("Paths leaked:")
for p in paths[:40]: print("  ", p)
# framework fingerprints
for pat in [r'Laravel[ /v]?(\d\.\d\.\d)', r'laravel/framework', r'CRMEB', r'crmeb', r'unionshop', r'Unishop', r'PHP\s+(\d\.\d+\.\d+)', r'Illuminate']:
    m=set(re.findall(pat, txt))
    if m: print(f"  {pat}: {m}")
# exception class
exc=set(re.findall(r'(NotFoundHttpException|Symfony\\\w+|Illuminate\\\w+\\\w+)', txt))
print("Exceptions/classes:", list(exc)[:15])
# look for any sensitive data
for kw in ["password","secret","password_hash","database","DB_","MYSQL","redis","token","key=","Bearer","http://127","http://192","127.0.0.1","localhost"]:
    if kw.lower() in txt.lower():
        i=txt.lower().find(kw.lower())
        print(f"  [{kw}] ...{plain[max(0,i-30):i+80]}...".replace("\n"," "))

print("\n=== HOMEPAGE fingerprint ===")
s,hb=get(base+"/")
open("ofa77_home.html","wb").write(hb)
htxt=hb.decode(errors="ignore")
for pat in [r'[Cc]RMEB', r'[Uu]nionshop', r'[Uu]nion[Ss]hop', r'unionshop', r'Laravel', r'Vue', r'version[:=]\s*["\']?[\d.]+', r'name="[^"]*version[^"]*"', r'/views/module/[\w/]+']:
    m=set(re.findall(pat, htxt))
    if m: print(f"  {pat}: {list(m)[:12]}")
# all module names
mods=sorted(set(re.findall(r'/views/module/([\w]+)', htxt)))
print("  modules:", mods)
# title
tm=re.search(r'<title>(.*?)</title>', htxt)
print("  title:", tm.group(1) if tm else "?")
