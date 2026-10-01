#!/usr/bin/env python3
"""並行探測 EMIC 同棧 21 個子域的存活情況"""
import urllib.request
import ssl
import concurrent.futures
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

SUBDOMAINS = [
    "portal2.emic.gov.tw", "hels2.emic.gov.tw", "gis2.emic.gov.tw",
    "giso.emic.gov.tw", "shels.emic.gov.tw", "sportal.emic.gov.tw",
    "tportal.emic.gov.tw", "tnda.emic.gov.tw", "sgis.emic.gov.tw",
    "dispweb.emic.gov.tw", "dispfile.emic.gov.tw", "dispwebt.emic.gov.tw",
    "oda2.emic.gov.tw", "nfadw.emic.gov.tw", "tgis.emic.gov.tw",
    "bear.emic.gov.tw", "bearo.emic.gov.tw", "sbear.emic.gov.tw",
    "bear2.emic.gov.tw", "bear3.emic.gov.tw", "bear4.emic.gov.tw",
]

def probe(sub):
    url = f"https://{sub}/"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
            return (sub, r.status, len(r.read(2048)), r.headers.get("Server", "-"), r.headers.get("Location", "-"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read(512).decode('utf-8', errors='replace').split('\n')[0][:200]
        except:
            pass
        return (sub, e.code, 0, e.headers.get("Server", "-"), body)
    except Exception as e:
        return (sub, "ERR", 0, str(e)[:80], "-")

if __name__ == "__main__":
    print(f"{'Subdomain':<26} {'Code':<5} {'Size':<8} {'RemoteIP':<18} {'Server':<25} {'Location/Title':<60}")
    print("-" * 140)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(probe, s): s for s in SUBDOMAINS}
        for f in concurrent.futures.as_completed(futs):
            sub, code, size, server, loc = f.result()
            print(f"{sub:<26} {str(code):<5} {str(size):<8} {'':<18} {server[:24]:<25} {loc[:58]:<60}")
