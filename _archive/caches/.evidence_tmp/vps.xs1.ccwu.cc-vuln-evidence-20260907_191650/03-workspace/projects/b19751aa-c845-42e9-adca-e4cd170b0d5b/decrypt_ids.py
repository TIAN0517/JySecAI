import base64, sys, json, urllib.request, ssl

KEY = b"absoietlj32fai12"  # AES-128 ECB key from bundle

def aes_ecb_dec(ct):
    try:
        from Crypto.Cipher import AES
        c = AES.new(KEY, AES.MODE_ECB)
        pt = c.decrypt(ct)
        pad = pt[-1]
        if 0 < pad <= 16 and pt.endswith(bytes([pad])*pad):
            pt = pt[:-pad]
        return pt
    except Exception as e:
        return None

def unwrap(enc):
    # outer base64 -> inner base64 string -> base64 -> ct
    try:
        inner = base64.b64decode(enc).decode()
        ct = base64.b64decode(inner)
        return ct
    except Exception:
        return None

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=15, context=ctx).read().decode("utf-8","replace")

endpoints = ["/api/v1/announ","/api/v1/contact","/api/v1/carousel","/api/v1/promo","/api/v2/game/turnover_rankings"]
ids = set()
for ep in endpoints:
    try:
        d = json.loads(get("https://www.ofa377.net"+ep))
        def walk(o):
            if isinstance(o, dict):
                for k,v in o.items():
                    if isinstance(v,str) and k.endswith("_id") and len(v)>16:
                        ids.add((k,v))
                    walk(v)
            elif isinstance(o, list):
                for i in o: walk(i)
        walk(d)
    except Exception as e:
        print(ep,"ERR",e)

print("collected", len(ids), "encrypted ids")
for k,v in sorted(ids):
    ct = unwrap(v)
    if not ct:
        print(f"{k} {v} -> (not b64-of-b64)"); continue
    pt = aes_ecb_dec(ct)
    print(f"{k:14s} ct_len={len(ct):2d} {v[:28]}... -> plaintext={pt}")
