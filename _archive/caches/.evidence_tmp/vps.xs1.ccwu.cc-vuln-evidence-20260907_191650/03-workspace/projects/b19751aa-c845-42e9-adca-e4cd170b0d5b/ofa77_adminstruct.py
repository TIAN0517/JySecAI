import httpx, re
c=httpx.Client(verify=False, follow_redirects=True, timeout=15,
    headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121 Safari/537.36'})
# extract JS from admin login page
r=c.get('https://ofa77.shop/module/admin/unionshop/user/login')
print('=== JS sources in admin login page ===')
for m in re.findall(r'<script[^>]*src="([^"]+)"', r.text):
    print('JS', m)
# inline hints
for kw in ['api','module','admin','unionshop','axios','fetch','url']:
    for m in re.findall(r'[^"\'\s]*'+kw+r'[^"\'\s]*', r.text, re.I)[:6]:
        if len(m)<80: print(f'  {kw}: {m}')

print('=== probe admin module paths ===')
paths=['module/admin/unionshop/','module/admin/unionshop/index','module/admin/unionshop/home',
'module/admin/unionshop/user','module/admin/unionshop/user/index','module/admin/unionshop/goods',
'module/admin/unionshop/order','module/admin/unionshop/setting','module/admin/unionshop/finance',
'module/admin/unionshop/promotion','module/admin/unionshop/decoration','module/admin/unionshop/statistic',
'module/admin/','module/admin/index','module/admin/unionshop/exit','module/admin/unionshop/password',
'module/admin/unionshop/user/password','module/admin/unionshop/user/resetpassword',
'module/admin/unionshop/user/forgot','module/admin/unionshop/forget','module/front/','module/front/index',
'module/admin/unionshop/api','module/admin/unionshop/upload','module/admin/unionshop/attachment']
for p in paths:
    try:
        rr=c.get('https://ofa77.shop/'+p)
        dbg='sf-dump' in rr.text
        # classify
        if rr.status_code in (301,302):
            loc=rr.headers.get('location','')
            tag=f'{rr.status_code} -> {loc[:50]}'
        elif dbg:
            tag='debug-dump(404)'
        else:
            tag=f'{rr.status_code} len={len(rr.content)}'
        # detect redirect to login (auth required)
        authed='login' in rr.text and 'logout' in rr.text
        print(f'{p:55} {tag}  auth-required={authed}')
    except Exception as e:
        print(p,'ERR',e)
