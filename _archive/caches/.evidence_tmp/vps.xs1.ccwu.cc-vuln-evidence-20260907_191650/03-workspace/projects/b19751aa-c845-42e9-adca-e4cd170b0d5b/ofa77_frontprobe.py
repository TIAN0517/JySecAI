import httpx, re
c=httpx.Client(verify=False, follow_redirects=True, timeout=15,
    headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121 Safari/537.36'})
# front home to find routes
print('=== front home ===')
try:
    h=c.get('https://ofa77.shop/')
    print('status',h.status_code,'len',len(h.content))
    for m in sorted(set(re.findall(r'href="(/[^"]+)"', h.text)))[:40]:
        print('  HREF', m)
    # look for api/js hints
    for kw in ['api','upload','register','login','user','cart']:
        for m in sorted(set(re.findall(r'[\"\']([^\"\']*'+kw+r'[^\"\']*)[\"\']', h.text, re.I)))[:5]:
            if len(m)<70: print(f'  {kw}: {m}')
except Exception as e: print('ERR',e)
print('=== front store paths ===')
for p in ['module/front/','index.html','index.php','category','goods','product','cart','member/login','member/register','member/index','user/login','user/register','cart/index','cart/add','upload','api','api/v1','.well-known/security.txt']:
    try:
        r=c.get('https://ofa77.shop/'+p)
        dbg='sf-dump' in r.text
        tag=f'{r.status_code} len={len(r.content)}' if not dbg else 'debug-dump'
        if r.status_code in(301,302): tag=f'{r.status_code}->{r.headers.get("location","")[:45]}'
        print(f'{p:25} {tag}')
    except Exception as e: print(p,'ERR',e)
