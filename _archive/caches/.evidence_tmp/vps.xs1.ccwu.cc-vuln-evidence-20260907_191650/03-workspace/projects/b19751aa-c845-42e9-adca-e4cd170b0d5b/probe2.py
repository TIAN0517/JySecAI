import httpx, json, random, urllib3, time
urllib3.disable_warnings()
BASE="https://ofa1777.ofa377.net/api"
H={"Content-Type":"application/json","Origin":"https://ofa1777.ofa377.net","Referer":"https://ofa1777.ofa377.net/"}
c=httpx.Client(verify=False,timeout=15)
def reg(phone, code, user="t1"):
    d={"bank_account":"123","bank_code":"CMB","bank_currency":"TWD","bank_name":"Test","email":"t%d@example.com"%random.randint(1,10**9),"line":"l1","name":"Test","password":"Passw0rd!123","phone_number":phone,"refer_code":"","username":user,"verify_code":code}
    r=c.post(BASE+"/v2/register/",data=json.dumps(d),headers=H)
    try: b=r.json()
    except: b={"raw":r.text[:150]}
    return r.status_code, b
P="886922222001"
c.post(BASE+"/v2/sms/send",data=json.dumps({"phone_number":P}),headers=H)
for code in ["1","12","123","1234","12345","123456","1234567","12345678","abc","12 34","1234\n"]:
    sc,b=reg(P, code)
    print(repr(code), "->", sc, b.get("error_code"), b.get("message"))
# also verify_email probe
r=c.get(BASE+"/v2/verify_email",params={"email":"t1@example.com"},headers=H)
print("verify_email:", r.status_code, r.text[:150])
# login probe wrong
d={"username":"t1","password":"Passw0rd!123","device_id":"dev123"}
r=c.post(BASE+"/v1/login",data=json.dumps(d),headers=H)
print("login wrong:", r.status_code, r.text[:200])
