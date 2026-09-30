#!/usr/bin/env python3
"""
Deep search for hidden content and API endpoints
"""

import requests
import re

sess = requests.Session()
sess.verify = False
sess.headers.update({'Host': 'www.af-search.119.gov.taipei'})

# Get the 4935-byte content
r = sess.get("https://210.69.42.55/", timeout=10)
content = r.text

print("=== Searching for hidden content ===")

# Look for comments, hidden fields, data attributes
comments = re.findall(r'<!--.*?-->', content, re.DOTALL)
if comments:
    print(f"Found {len(comments)} HTML comments")
    for c in comments[:3]:
        print(f"  {c[:200]}")

# Look for data-* attributes that might contain API endpoints
data_attrs = re.findall(r'data-[\w-]+=["\']([^"\']+)["\']', content)
if data_attrs:
    print(f"\nFound {len(data_attrs)} data attributes")
    for attr in data_attrs[:10]:
        print(f"  {attr[:100]}")

# Look for unusual script tags with embedded URLs
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
print(f"\n=== Analyzing {len(scripts)} script tags ===")

for i, script in enumerate(scripts):
    # Look for URLs in scripts
    urls = re.findall(r'https?://[^"\'>\s]+', script)
    if urls:
        print(f"\nScript {i+1} URLs:")
        for url in urls[:5]:
            print(f"  {url}")

# Look for any endpoint-like patterns
endpoints = re.findall(r'(?:/[a-zA-Z0-9_/-]+(?:/[a-zA-Z0-9_/-]+)*)', content)
unique_endpoints = list(set(e for e in endpoints if len(e) > 5))
print(f"\n=== Potential endpoints ({len(unique_endpoints)}) ===")
for ep in unique_endpoints[:15]:
    print(f"  {ep}")