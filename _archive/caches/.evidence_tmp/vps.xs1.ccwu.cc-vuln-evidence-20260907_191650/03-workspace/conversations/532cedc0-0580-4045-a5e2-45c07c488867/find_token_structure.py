import requests, json, urllib3, re
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
# 获取所有 JS 文件, 搜索 token 构造/解码相关
js_files=["js/app.js","js/auth.js","js/AuthService.js","js/services.js","js/controllers.js","js/index.js"]
for jf in js_files:
    try:
        r=s.get(BASE+"/"+jf, timeout=10)
        if r.status_code==200:
            t=r.text
            # 搜索 token 相关
            for pat in [r"jwt[^;]{0,80}", r"token[^;]{0,60}", r"decode[^;]{0,60}", 
                        r"payload[^;]{0,60}", r"localStorage[^;]{0,60}", r"userToken[^;]{0,60}"]:
                for m in set(re.findall(pat, t, re.I)):
                    if any(k in m.lower() for k in ["decode","payload","jwt","local","usertoken","verify"]):
                        print(f"[{jf}] {m[:100]}")
    except: pass
print("DONE")
