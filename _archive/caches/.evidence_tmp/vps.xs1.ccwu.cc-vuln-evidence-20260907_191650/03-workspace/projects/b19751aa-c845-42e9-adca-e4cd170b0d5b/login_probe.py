import requests, urllib3
urllib3.disable_warnings()
H = {"User-Agent":"Mozilla/5.0 (X11; Linux x86_64)","Content-Type":"application/json",
     "Origin":"https://epcr.tpf.gov.tw:4004","Referer":"https://epcr.tpf.gov.tw:4004/"}

def try_login(label, payload, fresh_session=True):
    S = requests.Session(); S.verify=False
    if fresh_session:
        try:
            c = S.get("https://epcr.tpf.gov.tw:4004/captcha?t=1", timeout=12, headers=H)
            has_captcha = c.status_code==200 and len(c.content)>100
        except Exception:
            has_captcha=False
    else:
        has_captcha = False
    try:
        r = S.post("https://epcr.tpf.gov.tw:4004/login", json=payload, timeout=15, headers=H)
        print(f"[{label}] captcha_session={has_captcha} => {r.status_code} {r.text[:180]!r}")
        for k in ("Set-Cookie","x-powered-by","content-type"):
            if k in r.headers: print(f"      {k}: {r.headers[k]}")
    except Exception as e:
        print(f"[{label}] EXC {e}")

try_login("empty", {})
try_login("no-domain", {"username":"admin","password":"admin","captcha":"abcde"})
try_login("with-domain", {"username":"admin","password":"admin","captcha":"abcde","domain":"AUTH_SERVER"})
try_login("creds-only", {"username":"admin","password":"admin"})
try_login("no-captcha-session", {"username":"admin","password":"admin","captcha":"abcde","domain":"AUTH_SERVER"}, fresh_session=False)
