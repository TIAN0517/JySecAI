#!/usr/bin/env python3
"""Search all extracted data for URLs, admin paths, backend references."""
import json, re

fpath = "/mnt/c/Users/Administrator/Desktop/JySecAI/evidence/bf1788-wechatlogin-20260915/full_member_data_testwechat001.json"
d = json.load(open(fpath))
data = d["data"]

urls = set()
admin_refs = set()
for cmd, entry in data.items():
    resp = entry.get("response", {})
    body = json.dumps(resp, ensure_ascii=False)
    # Find all URLs
    found_urls = re.findall(r'https?://[^\s"]+', body)
    for u in found_urls:
        urls.add(u)
    # Find admin/backend references
    for kw in ['admin', 'backend', 'manage', 'console', 'phpmyadmin', 'cpanel', 'login']:
        if kw in body.lower() and 'wechatLogin' not in body and '請使用微信' not in body:
            admin_refs.add(f"cmd={cmd}: {kw}")

print("=== URLs found in responses ===")
for u in sorted(urls):
    print(f"  {u}")

print("\n=== Admin/backend references ===")
for r in sorted(admin_refs):
    print(f"  {r}")