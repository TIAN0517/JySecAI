import sys, time, json, requests, urllib3
urllib3.disable_warnings()
S = "https://epcr.tpf.gov.tw:4004"

def cycle(username, password, captcha_val, tag=""):
    s = requests.Session()
    # get captcha
    r = s.get(S + "/captcha", timeout=20)
    ct = r.headers.get("set-cookie", "")
    img = r.content
    with open("/opt/CyberStrikeAI/tmp/workspace/projects/b19751aa-c845-42e9-adca-e4cd170b0d5b/epcr/lastcap.png", "wb") as f:
        f.write(img)
    body = {"username": username, "password": password, "captcha": captcha_val, "domain": "AUTH_SERVER"}
    r2 = s.post(S + "/login", json=body, timeout=25, headers={"Content-Type": "application/json"})
    return r2.status_code, r2.text[:400], ct

if __name__ == "__main__":
    u, p, cv = sys.argv[1], sys.argv[2], sys.argv[3]
    code, text, ct = cycle(u, p, cv)
    print("HTTP", code)
    print("COOKIE", ct[:80])
    print("BODY", text)
