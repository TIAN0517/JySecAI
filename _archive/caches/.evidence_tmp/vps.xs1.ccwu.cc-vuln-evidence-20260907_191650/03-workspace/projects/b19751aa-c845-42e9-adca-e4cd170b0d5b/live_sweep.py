#!/usr/bin/env python3
import httpx, json, ssl, socket, concurrent.futures as cf, datetime, re

DOMAINS = ["momoshop.com.tw","24h.pchome.com.tw","etmall.com.tw","ego-finance.com.tw",
 "welend.hk","newloan.com.tw","shincredit.com.tw","superbank.com.tw","tac.finance","tac.com.tw",
 "he-jing.com.tw","hfcfinance.com.tw","megaholdings.com.tw","easyauction.com.tw","hotains.com.tw",
 "hotaimotor.com.tw","hotaimember.com.tw","ec2.hotains.com.tw","kuanzho.com.tw","tzuchi.org.tw","tzuchi.org.hk"]

def host_variants(d):
    out=[]
    for base in (d,"www."+d):
        out.append(base)
    return out

def tls_probe(host, port=443, timeout=8):
    try:
        ctx=ssl.create_default_context()
        with socket.create_connection((host,port),timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as s:
                v=s.version()
                try:
                    c=s.getpeercert()
                    org=issuer=cn=""
                    for f in c.get("subject",[]):
                        for a,b in f:
                            if a=="organizationName": org=b
                            if a=="commonName": cn=b
                    for f in c.get("issuer",[]):
                        for a,b in f:
                            if a=="organizationName": issuer=b
                    return dict(tls=v, subject_cn=cn, issuer=issuer, not_after=c.get("notAfter",""))
                except ssl.CertificateError:
                    return dict(tls=v, subject_cn=None, issuer="NOVERIFY", not_after="")
    except Exception as e:
        return dict(tls_err=str(e)[:60])

def probe(base, scheme, timeout=12):
    url=f"{scheme}://{base}"
    r={}
    try:
        with httpx.Client(verify=False, follow_redirects=True, timeout=timeout,
                          headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}) as c:
            resp=c.get(url)
            r["status"]=resp.status_code
            r["final_url"]=str(resp.url)
            r["server"]=resp.headers.get("server","")
            r["xpowered"]=resp.headers.get("x-powered-by","")
            r["setcookie"]=list(resp.headers.get_list("set-cookie"))[:4]
            r["len"]=len(resp.content)
            html=resp.content[:12000].decode("utf-8","ignore")
            tech=[]
            for pat,name in [(r'wp-content','WordPress'),(r'laravel','Laravel'),(r'__CF-','Cloudflare'),(r'ASP\.NET|\.aspx|__VIEWSTATE','.NET/IIS'),
                             (r'PHPSESSID|JSESSIONID','PHP/Java'),(r'node_modules|react|vue','JS-Framework'),(r'Spring|javax\.','Java/Spring'),
                             (r'<meta name="generator" content="([^"]+)"','Generator'),(r'nginx','Nginx'),(r'Apache','Apache'),
                             (r'Powered by|CMS','CMS'),(r'drupal','Drupal'),(r'joomla','Joomla')]:
                m=re.search(pat, html, re.I)
                if m:
                    tech.append(m.group(1) if m.lastindex else name)
            r["tech"]=tech
            r["title"]=(re.search(r'<title[^>]*>(.*?)</title>', html, re.I|re.S) or [None,""])[1].strip()[:120]
            # detect generator
            mg=re.search(r'<meta name="generator" content="([^"]+)"', html, re.I)
            if mg: r["generator"]=mg.group(1)
    except Exception as e:
        r["err"]=str(e)[:90]
    return r

def work(d):
    res={"domain":d,"probes":{}}
    for base in host_variants(d):
        for scheme in ("https","http"):
            r=probe(base,scheme)
            res["probes"][f"{scheme}://{base}"]=r
    # TLS probe on www
    if "www."+d not in [d]:
        res["tls_w"]=tls_probe("www."+d)
        res["tls_apex"]=tls_probe(d)
    return res

out=[]
with cf.ThreadPoolExecutor(max_workers=10) as ex:
    for w in ex.map(work, DOMAINS):
        out.append(w)
json.dump(out, open("live_sweep.json","w"), ensure_ascii=False, indent=1)

# print compact
for w in out:
    print("="*70)
    print(w["domain"])
    for k,r in w["probes"].items():
        if r.get("err"):
            print(f"  {k:38} ERR {r['err']}")
        else:
            tech=",".join(r.get("tech",[])[:5])
            print(f"  {k:38} {r.get('status')} srv={r.get('server','')[:30]:30} tech=[{tech}] title={str(r.get('title',''))[:40]}")
    for tk in ("tls_w","tls_apex"):
        if tk in w:
            t=w[tk]
            if "tls_err" in t: print(f"  {tk}: {t['tls_err']}")
            else: print(f"  {tk}: {t.get('tls')} cn={t.get('subject_cn')} issuer={t.get('issuer')} exp={t.get('not_after')}")
