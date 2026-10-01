import httpx, json
UA={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121 Safari/537.36','Content-Type':'application/json','Origin':'https://ofa1777.ofa377.net','Referer':'https://ofa1777.ofa377.net/'}
B='https://ofa1777.ofa377.net'
c=httpx.Client(verify=False, timeout=15, headers=UA)
print('=== 301 targets ===')
for p in ['/api/v1/bet','/api/v1/order','/api/v1/agent']:
    r=c.get(B+p)
    print(p,'->',r.status_code,'loc=',r.headers.get('location'))
print('=== login param discovery (target: escape 422 reject) ===')
combos=[
 {'username':'tester1','password':'x'},{'user':'tester1','password':'x'},{'account':'tester1','password':'x'},
 {'name':'tester1','password':'x'},{'mobile':'123456789','password':'x'},{'phone':'123456789','password':'x'},
 {'user_name':'tester1','pass':'x'},{'login':'tester1','pwd':'x'},{'email':'t@t.com','password':'x'},
 {'username':'tester1','password':'x','code':'1234'},{'username':'tester1','password':'x','verify':'1234'}]
for d in combos:
    try:
        r=c.post(B+'/api/v1/login', data=json.dumps(d).encode())
        print(json.dumps(d),'->',r.status_code, r.text[:70].replace('\n',' '))
    except Exception as e: print(d,'ERR',e)
print('=== register param discovery ===')
rcom=[{'username':'ofatest01','password':'OfaTest#2024','email':'ofatest01@ofa377.local'},
 {'username':'ofatest01','password':'OfaTest#2024'},{'name':'ofatest01','password':'OfaTest#2024','email':'ofatest01@ofa377.local'},
 {'mobile':'0912345678','password':'OfaTest#2024','code':'1234'},{'account':'ofatest01','password':'OfaTest#2024'}]
for d in rcom:
    try:
        r=c.post(B+'/api/v1/register', data=json.dumps(d).encode())
        print(json.dumps(d)[:55],'->',r.status_code, r.text[:80].replace('\n',' '))
    except Exception as e: print(d,'ERR',e)
print('=== config/system/version (GET) ===')
for p in ['/api/v1/config','/api/v1/system','/api/v1/version','/api/v1/info','/api/v1/status','/api/v1/online/config','/api/v1/getconfig']:
    try:
        r=c.get(B+p); print(p,'->',r.status_code, r.text[:90].replace('\n',' '))
    except Exception as e: print(p,'ERR',e)
c.close()
