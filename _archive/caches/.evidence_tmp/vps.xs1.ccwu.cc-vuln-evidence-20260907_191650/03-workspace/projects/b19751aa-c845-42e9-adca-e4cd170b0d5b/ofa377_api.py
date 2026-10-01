import httpx, json
UA={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121 Safari/537.36'}
for base in ['https://ofa1777.ofa377.net','https://ofa377.net']:
    print(f'=== {base} ===')
    c=httpx.Client(verify=False, timeout=15, headers={**UA,'Origin':base,'Referer':base+'/'})
    # base + known
    for p in ['','/','/api','/api/','/api/v1','/api/v1/online','/api/v1/config','/api/v1/system',
              '/api/v1/member','/api/v1/user','/api/v1/user/info','/api/v1/login','/api/v1/register',
              '/api/v1/bet','/api/v1/order','/api/v1/agent','/api/v1/promo','/api/v1/ann',
              '/api/v1/announcement','/api/v1/version','/health','/api/v1/health','/swagger',
              '/api/swagger','/api/docs','/debug','/metrics']:
        for m in ['GET','POST']:
            try:
                kw={'json':{'username':'x','password':'x'}} if (m=='POST' and ('login' in p or 'register' in p)) else ({'a':1} if m=='POST' else {})
                r=c.request(m, base+p, data=None if m=='GET' else kw)
                ct=r.headers.get('content-type','')[:20]
                body=r.text[:90].replace('\n',' ')
                if r.status_code not in (404,) or 'api/v1/online' in p:
                    print(f'{m:5} {p:28} {r.status_code} {ct:20} {body}')
            except Exception as e: pass
    c.close()
