import requests, urllib3, json
urllib3.disable_warnings()
S = "https://epcr.tpf.gov.tw:4004"

def raw_login(username, password, captcha, with_captcha=True, domain="AUTH_SERVER"):
    s = requests.Session()
    rc = s.get(S + "/captcha", timeout=20)
    cap_cookie = rc.headers.get("set-cookie", "")
    body = {"username": username, "password": password, "domain": domain}
    if with_captcha:
        body["captcha"] = captcha
    r = s.post(S + "/login", data=json.dumps(body), headers={"Content-Type": "application/json"}, timeout=25)
    req_cookie = r.request.headers.get("cookie", "")
    return rc.status_code, cap_cookie, r.status_code, r.headers.get("set-cookie",""), r.text[:300], req_cookie

print("=== A) session cookie persistence check ===")
# fresh session, print captcha Set-Cookie then what cookie is SENT on login
code1, cap_cookie, code2, login_cookie, body, sent_cookie = raw_login("admin", "wrongpass", "abcde")
print("captcha status:", code1)
print("captcha Set-Cookie:", cap_cookie[:90])
print("cookie SENT on login:", sent_cookie[:90])
print("login status:", code2)
print("login Set-Cookie:", login_cookie[:90])
print("login body:", body)
