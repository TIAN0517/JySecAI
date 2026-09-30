#!/usr/bin/env python3
"""Phase 19: Deep content extraction from live proxy-accessible hosts."""
import requests, urllib3, re, json, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
PROXY = {"https": "socks5h://202.160.76.154:11085"}
s = requests.Session()
s.headers.update(HEADERS)
s.verify = False
s.proxies = PROXY

def probe(url, timeout=15):
    try:
        r = s.get(url, timeout=timeout, allow_redirects=True)
        t = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I | re.S)
        title = t.group(1).strip()[:300] if t else ""
        has_form = "<form" in r.text.lower()
        has_pw = "password" in r.text.lower() or "密碼" in r.text
        # Find login-related links
        links = re.findall(r'(?:href|action)=["\']([^"\']+)["\']', r.text)
        login_links = [l for l in links if any(w in l.lower() for w in ['login', 'admin', 'auth', 'token', 'signin', 'account'])]
        # Find JS files
        js = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', r.text)
        return {
            "url": url,
            "final_url": r.url,
            "status": r.status_code,
            "len": len(r.text),
            "title": title,
            "has_form": has_form,
            "has_pw": has_pw,
            "content_type": r.headers.get("Content-Type", ""),
            "server": r.headers.get("Server", ""),
            "login_links": login_links[:20],
            "js_files": js[:10],
            "body_preview": r.text[:2000],
        }
    except Exception as e:
        return {"url": url, "error": str(e)[:200]}

# === FSM PROBES ===
print("=== FSM 119 (fsm.119.gov.taipei via proxy) ===")
fsm_results = []
for path in ["/", "/w/fsm119/index", "/login", "/admin/login", "/auth/genToken",
             "/auth/fetchServerData", "/oauth/token", "/api/getUserToken", "/sso/login",
             "/cas/login", "/user/login"]:
    url = f"https://fsm.119.gov.taipei{path}"
    r = probe(url)
    fsm_results.append(r)
    print(f"  {path}: {r.get('status', 'ERR')} | len={r.get('len',0)} | title={r.get('title','')[:40]}")
    if r.get('login_links'):
        print(f"    links: {r['login_links'][:5]}")
    if r.get('body_preview'):
        with open(f"tpe119_evidence/login_pages/fsm_{path.replace('/','_').replace('.','_')}.html", "w") as f:
            f.write(r["body_preview"][:8000])
    time.sleep(0.5)

# === EPCR PROBES ===
print("\n=== EPCR (118.163.107.93 via proxy) ===")
epcr_results = []
for port in [4000, 4001, 4002]:
    url = f"https://118.163.107.93:{port}/"
    r = probe(url)
    epcr_results.append(r)
    print(f"  :{port}: {r.get('status', 'ERR')} | len={r.get('len',0)} | title={r.get('title','')[:40]} | ct={r.get('content_type','')}")
    if r.get('login_links'):
        print(f"    links: {r['login_links'][:5]}")
    if r.get('body_preview'):
        with open(f"tpe119_evidence/login_pages/epcr_{port}.html", "w") as f:
            f.write(r["body_preview"][:8000])
    time.sleep(0.5)
    # Also probe common paths on each port
    for path in ["/login", "/admin", "/api/login", "/auth/login"]:
        url2 = f"https://118.163.107.93:{port}{path}"
        r2 = probe(url2, timeout=8)
        if r2.get('status') == 200:
            print(f"  :{port}{path}: 200 | len={r2.get('len',0)} | form={r2.get('has_form')} pw={r2.get('has_pw')}")
        elif r2.get('status') == 404:
            pass  # skip 404s
        time.sleep(0.3)

results = {"fsm": fsm_results, "epcr": epcr_results}
with open("tpe119_evidence/phase19_live_content.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nFull results saved to tpe119_evidence/phase19_live_content.json")
