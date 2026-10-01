import json, urllib.request
from concurrent.futures import ThreadPoolExecutor

subs = ["","www","admin","api","app","blog","dev","test","shop","mail","panel","portal",
 "login","ctf","challenge","pwn","download","m","beta","demo","status","dashboard",
 "webmail","ns1","git","old","internal","secure","home","bbs","pay","account","v1","pre"]

def check(s):
    name = (s+".csogmes168.com") if s else "csogmes168.com"
    try:
        with urllib.request.urlopen(f"https://dns.google/resolve?name={name}&type=A", timeout=4) as r:
            d=json.load(r)
        ans=d.get("Answer",[])
        if ans: return (name, [a.get("data") for a in ans])
        return (name, None)
    except Exception:
        return (name, "?")

res={}
with ThreadPoolExecutor(max_workers=25) as ex:
    for name,val in ex.map(check, subs):
        res[name]=val
hits=[f"{k} -> {v}" for k,v in res.items() if isinstance(v,list) and v]
print("RESOLVED:", hits if hits else "(none)")
print("DONE", len(res))
