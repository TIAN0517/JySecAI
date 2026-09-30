#!/usr/bin/env python3
"""Phase 13: Get actual login page HTML for all LIVE login endpoints."""
import requests, urllib3, json, os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {"https": "socks5h://202.160.76.155:11084"}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# Live login endpoints to probe - both direct + via proxy
LOGIN_PROBES = {
    "tpertc.tfd.gov.tw": {
        "urls": ["https://{host}", "https://{host}/rtc/account.php", "https://{host}/login"],
        "use_proxy": True
    },
    "210.69.43.112": {
        "urls": ["https://{host}/", "https://{host}/login", "https://{host}/admin/login"],
        "use_proxy": False
    },
    "appservice119.tfd.gov.tw": {
        "urls": ["https://{host}/", "https://{host}/login"],
        "use_proxy": True
    },
    "210.69.43.103": {
        "urls": ["https://{host}/"],
        "use_proxy": False
    },
}

os.makedirs("tpe119_evidence/login_pages", exist_ok=True)
results = {}

for host_key, cfg in LOGIN_PROBES.items():
    proxies = PROXY if cfg.get("use_proxy") else None
    host_results = []
    for url_template in cfg["urls"]:
        url = url_template.format(host=host_key)
        try:
            r = requests.get(url, proxies=proxies, headers=HEADERS, verify=False, timeout=15, allow_redirects=True)
            result = {
                "url": url,
                "status": r.status_code,
                "server": r.headers.get("Server", ""),
                "content_length": len(r.content),
                "title": "",
                "has_form": "form" in r.text.lower() or "input" in r.text.lower(),
                "login_indicators": [],
            }
            # Extract title
            import re
            t = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I | re.S)
            if t:
                result["title"] = t.group(1).strip()[:200]
            
            # Check for login indicators
            text_lower = r.text.lower()
            indicators = ["password", "login", "account", "username", "signin", "log in", "登入", "密碼", "帳號", "sign in"]
            found = [i for i in indicators if i in text_lower]
            result["login_indicators"] = found[:10]
            
            # Save HTML
            filename = f"login_pages/{host_key.replace('.', '_').replace(':', '_')}_status{r.status_code}.html"
            with open(f"tpe119_evidence/{filename}", "w") as f:
                f.write(r.text[:5000])
            
            host_results.append(result)
        except Exception as e:
            host_results.append({"url": url, "error": str(e)[:200]})
    results[host_key] = host_results

with open("tpe119_evidence/login_pages_summary.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(json.dumps(results, indent=2, ensure_ascii=False))
