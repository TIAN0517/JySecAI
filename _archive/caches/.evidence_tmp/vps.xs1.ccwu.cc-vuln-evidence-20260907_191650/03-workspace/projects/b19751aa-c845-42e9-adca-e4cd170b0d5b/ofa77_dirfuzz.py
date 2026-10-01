import httpx, sys
from concurrent.futures import ThreadPoolExecutor
c=httpx.Client(verify=False, follow_redirects=True, timeout=15,
    headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121 Safari/537.36'})
base='https://ofa77.shop/'
paths=[l.strip() for l in open('ofa77_paths.txt') if l.strip()]
def probe(p):
    u=base+p
    try:
        r=c.get(u)
        dbg='sf-dump' in r.text
        ng404='404 Not Found' in r.text or r.status_code==404
        # keep: 200/301/302/401/403/500 that is NOT a debug dump and NOT nginx 404
        keep=(r.status_code in (200,301,302,401,403,500)) and not dbg and not ng404
        if keep:
            print(f'{r.status_code} len={len(r.content):7} {p}')
        return (p, r.status_code, len(r.content), dbg, ng404)
    except Exception as e:
        return (p, -1, 0, False, False)
with ThreadPoolExecutor(max_workers=6) as ex:
    res=list(ex.map(probe, paths))
print('---- done, total', len(res))
