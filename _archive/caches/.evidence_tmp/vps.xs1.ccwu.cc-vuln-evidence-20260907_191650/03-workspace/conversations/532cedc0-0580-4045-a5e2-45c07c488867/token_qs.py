import requests, urllib3, re
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
r=s.get(BASE+"/js/app.js", timeout=15)
t=r.text
# 找 tokenQs 完整上下文
for m in re.finditer(r'tokenQs', t):
    start=max(0,m.start()-300); end=min(len(t),m.end()+400)
    print("=== tokenQs 上下文 ===")
    print(t[start:end])
    print()
