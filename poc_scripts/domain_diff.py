#!/usr/bin/env python3
"""
Compare content between IP-based and domain-based requests
"""

import requests
import difflib

sess = requests.Session()
sess.verify = False

# Get content via IP with Host header
print("=== Fetching via IP with Host header ===")
sess.headers.update({'Host': 'www.af-search.119.gov.taipei'})
r1 = sess.get("https://210.69.42.55/", timeout=10)
content1 = r1.text

print(f"Size: {len(content1)} bytes")

# Get content via direct domain (simulated - using IP to resolve)
print("\n=== Key differences to look for ===")

# Look for unique elements
unique_patterns = [
    "api", "dispatch", "notify", "push", "triage",
    "user", "admin", "pushover", "telegram", "notify"
]

for pattern in unique_patterns:
    if pattern in content1.lower():
        # Find context
        idx = content1.lower().find(pattern)
        snippet = content1[max(0, idx-100):idx+100]
        if '<' in snippet or '>' in snippet:
            print(f"  Found '{pattern}' in HTML context")
        else:
            print(f"  Found '{pattern}' in text: {snippet[:150]}")

# Look for href links
import re
href_pattern = r'href=["\']([^"\']+)["\']'
href_matches = re.findall(href_pattern, content1)
print(f"\n=== All links found ({len(href_matches)}) ===")
for href in href_matches[:20]:  # Show first 20
    if href.startswith('http'):
        print(f"  {href}")
    else:
        print(f"  /{href}")

# Look for API endpoints in JavaScript
script_pattern = r'<script[^>]*>(.*?)</script>'
scripts = re.findall(script_pattern, content1, re.DOTALL)
print(f"\n=== Script content analysis ({len(scripts)} scripts) ===")
for i, script in enumerate(scripts[:3]):  # Check first 3 scripts
    if 'api' in script.lower() or 'fetch' in script.lower():
        print(f"  Script {i+1} contains API-related code")
        # Extract fetch calls
        fetch_pattern = r'fetch\s*\(\s*["\']([^"\']+)["\']'
        fetches = re.findall(fetch_pattern, script)
        for f in fetches:
            if 'api' in f or 'dispatch' in f:
                print(f"    -> API endpoint: {f}")