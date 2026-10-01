import requests, urllib3, re
urllib3.disable_warnings()
S = requests.Session(); S.verify=False
UA={"User-Agent":"Mozilla/5.0"}
G="http://35.234.50.28:8000"

r=S.get(G+"/index.html", timeout=10, headers=UA)
html=r.text
js=[m for m in re.findall(r'src="([^"]+\.js)"', html)]
print("index.html JS bundles:")
for j in js: print("  ",j)

# also check for app.js / main bundle
all_js=set(js)
for extra in ["/js/app.js","/js/main.js","/app.js","/js/bundle.js","/js/ePcR.js","/js/EPCR.js"]:
    all_js.add(extra)

print("\n===== grep socket.io / namespace / io( / events across JS =====")
found={}
for j in sorted(all_js):
    u = j if j.startswith("http") else G+j
    try:
        t=S.get(u, timeout=10, headers=UA).text
    except Exception: continue
    if not t: continue
    hits=set()
    for pat in [r'io\s*\(\s*[\'"]([^\'"]+)', r'\.io\s*\(', r'socket\s*=\s*io', r'\.on\s*\(\s*[\'"]([a-zA-Z_$]+)[\'"]', r'\.emit\s*\(\s*[\'"]([a-zA-Z_$]+)[\'"]', r'namespace', r'JWT_SECRET', r'[Ss]ecret\s*[:=]', r'jsonwebtoken', r'jwtOptions']:
        for m in re.findall(pat, t):
            hits.add(m)
    if hits:
        print(f"  {j} :: {sorted(hits)[:25]}")
        found[j]=t

# dump the main app.js region around socket.io
for j,t in found.items():
    for m in re.finditer(r'io\s*\(', t):
        s=max(0,m.start()-80); print(f"\n  [socket.io @ {j}] {t[s:m.start()+120]!r}")
        break
print("done")
