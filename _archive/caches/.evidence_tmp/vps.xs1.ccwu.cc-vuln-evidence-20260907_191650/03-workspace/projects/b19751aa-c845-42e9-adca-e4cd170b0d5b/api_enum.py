import requests, urllib3, re
urllib3.disable_warnings()
S=requests.Session(); S.verify=False
UA={"User-Agent":"Mozilla/5.0"}
G="http://35.234.50.28:8000"

r=S.get(G+"/index.html",timeout=10,headers=UA)
js=[m for m in re.findall(r'src="js/[^"]+\.js"', r.text)]
paths=set()
for j in js:
    u=G+"/"+j[5:]
    try: t=S.get(u,timeout=10,headers=UA).text
    except Exception: continue
    # api path patterns
    for m in re.findall(r'["\'](/(?:api|epcr|user|users|hospital|branch|emt|device|dispatch|case|vital|print|stat|monitor|mci|resource|permission|role|supplies|ohca|pcr)[^"\']{0,60})["\']', t):
        paths.add(m)
    # template urls with interpolation
    for m in re.findall(r'["\']([^"\']*\{\{[^}]+\}\}[^"\']*?(?:/\w+)+)', t):
        paths.add(m.replace("{{","{").replace("}}","}"))
# socket.io usage
sio_files={}
for j in js:
    u=G+"/"+j[5:]
    try: t=S.get(u,timeout=10,headers=UA).text
    except Exception: continue
    for pat in [r'\bio\(\s*([^)]{1,80})', r'socket[^;]{0,60}\.on\(\s*["\'](\w+)', r'\.emit\(\s*["\'](\w+)']:
        for mm in re.findall(pat,t):
            sio_files.setdefault(j,set()).add(mm)

print(f"=== extracted {len(paths)} API path patterns ===")
for p in sorted(paths)[:80]: print("  ",p)
print(f"\n=== socket.io references (file -> [io() arg / .on / .emit]) ===")
for f,v in sio_files.items(): print("  ",f,"::",sorted(v)[:20])

# Now test a curated set unauthenticated
test=[p for p in paths if p.count("{")==0][:40]
print(f"\n=== unauth test on {G} (no JWT) ===")
for p in test:
    for m in ["GET","POST"]:
        try:
            rr=S.request(m,G+p,timeout=8,headers=UA,data="{}" if m=="POST" else None)
            tag="OPEN?" if rr.status_code in (200,201) else ""
            if rr.status_code in (200,201) or rr.status_code not in (401,403,404):
                print(f"  [{rr.status_code}] {m} {p} {tag} :: {rr.text[:50]!r}")
        except Exception: pass
print("done")
