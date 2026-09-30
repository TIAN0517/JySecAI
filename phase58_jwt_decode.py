#!/usr/bin/env python3
"""Phase 58: Decode JWT + use against NCDR API."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, base64, re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5://202.160.76.154:11085', 'http': 'socks5://202.160.76.154:11085'}

# Read the env file
with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe_service119_live.env', 'r') as f:
    content = f.read()

# Extract JWT
jwts = re.findall(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', content)
print(f"=== Found {len(jwts)} JWT(s) ===")
jwt = jwts[0] if jwts else None
if jwt:
    print(f"JWT (truncated): {jwt[:80]}...")
    
    # Decode it (without verification)
    parts = jwt.split('.')
    if len(parts) == 3:
        header = base64.urlsafe_b64decode(parts[0] + '==')
        payload = base64.urlsafe_b64decode(parts[1] + '==')
        try:
            print(f"\nHeader: {json.loads(header)}")
            print(f"Payload: {json.dumps(json.loads(payload), indent=2)}")
        except Exception as e:
            print(f"Decode error: {e}")

# Context around the JWT
print("\n=== Context in env file ===")
for line in content.split('\n'):
    if 'jwt' in line.lower() or 'token' in line.lower() or 'jwt' in line.lower():
        print(f"  {line.strip()[:200]}")

# Also check for other auth-related values
print("\n=== All env vars ===")
for line in content.split('\n'):
    if line.strip() and '=' in line:
        key = line.split('=')[0].strip()
        print(f"  {key}")
