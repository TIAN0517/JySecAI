#!/usr/bin/env python3
"""Phase 67: Parse EPCR exfiltrated data - final summary."""
import json, re
from collections import Counter

with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/epcr_jwt_exploit_results.json', 'r') as f:
    data = json.load(f)

print("=" * 70)
print("EPCR AUTH SERVER JWT BYPASS — FULL COMPROMISE REPORT")
print("=" * 70)

# Config
config = json.loads(data['/config']['body'])
print(f"\n### Server Configuration")
print(f"  JWT_SECRET: {config.get('JWT_PASSWORD', 'N/A')}")
print(f"  Captcha session secret: {config.get('captcha', {}).get('sessionSecret', 'N/A')}")
print(f"  fail2ban: enabled={config.get('fail2ban_enable')}, threshold={config.get('fail2ban_count')} failures")
print(f"  Max idle: {config.get('MAX_IDLE_DURATION', 'N/A')}ms")
print(f"  JWT expiry: {config.get('JWT_TOKEN_EXPIRE', 'N/A')}s")

# Users
users = json.loads(data['/Users']['body'])
print(f"\n### {len(users)} User Accounts Extracted")
print(f"  Roles breakdown:")
role_counts = Counter(u.get('Role', {}).get('name', 'N/A') if isinstance(u.get('Role'), dict) else u.get('RoleName', 'N/A') for u in users)
for role, count in role_counts.most_common():
    print(f"    {role}: {count}")

print(f"\n  Admin accounts:")
for u in users:
    role_obj = u.get('Role', {})
    role_name = role_obj.get('name', 'N/A') if isinstance(role_obj, dict) else str(role_obj)
    if role_name == 'ADMIN':
        token2fa = u.get('token2FA') or 'N/A'
        print(f"    [{u['id']}] {u['name']} / {u['account']} / 2FA: {u.get('use2FA', False)} / token: {token2fa[:20] if token2fa != 'N/A' else token2fa}...")

print(f"\n  Active service accounts:")
for u in users:
    if u.get('account', '').startswith('__'):
        role_name = u.get('Role', {}).get('name', 'N/A') if isinstance(u.get('Role'), dict) else str(u.get('Role', 'N/A'))
        print(f"    [{u['id']}] {u['account']} / role: {role_name}")

# Roles
roles = json.loads(data['/Roles']['body'])
print(f"\n### Roles & Permissions ({len(roles)} roles)")
for role in roles[:5]:
    perms = [p['name'] for p in role.get('Permissions', [])]
    print(f"  [{role['id']}] {role['name']}: {len(perms)} permissions")
if len(roles) > 5:
    print(f"  ... and {len(roles)-5} more roles")

# Permissions
perms = json.loads(data['/Permissions']['body'])
print(f"\n### All Permissions ({len(perms)} total)")
for p in perms:
    print(f"  [{p['id']}] {p['name']}")

# Key findings
print(f"\n### Exploitation Summary:")
print(f"  1. JWT secret exposed via /config: {config.get('JWT_PASSWORD')}")
print(f"  2. Forged JWT accepted at ?token= parameter (auth bypass)")
print(f"  3. Full DB dumped: {len(users)} users, {len(roles)} roles, {len(perms)} permissions")
print(f"  4. Admin 2FA token: {next((u.get('token2FA','N/A') for u in users if u.get('account')=='admin'), 'N/A')}")
print(f"  5. POST /Users + POST /Roles accepted (account injection possible)")
print(f"  6. Fail2ban enabled but bypassable (no failed logins needed with JWT)")

print(f"\n### Files Saved:")
print(f"  Raw data: epcr_jwt_exploit_results.json (in tpe119_evidence/)")
print(f"  Full report: tpe119_evidence/ncdr_api_exploitation.md + 地毯搜索_119登入口報告.md")
