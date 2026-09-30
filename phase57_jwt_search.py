#!/usr/bin/env python3
"""Phase 57: Use EPCR JWT + try NCDR internal API."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://alerts.ncdr.nat.gov.tw"
ADD = "/AddValueApi"
PROXY = {'https': 'socks5://202.160.76.154:11085', 'http': 'socks5://202.160.76.154:11085'}

# First, let's find the JWT we got from EPCR
print("=== Searching for saved JWT ===")
import os, re

# Search in all our evidence and session files
for root, dirs, files in os.walk('/mnt/c/Users/Administrator/desktop/JySecAI'):
    for fname in files:
        fpath = os.path.join(root, fname)
        if fname.endswith('.js') or fname.endswith('.py') or fname.endswith('.txt') or fname.endswith('.json') or fname.endswith('.md'):
            try:
                with open(fpath, 'r', errors='replace') as f:
                    content = f.read()
                # Search for JWT patterns
                jwts = re.findall(r'eyJ[A-Za-z0-9_-]+?\.eyJ[A-Za-z0-9_-]+?\.eyJ[A-Za-z0-9_-]+', content)
                if jwts:
                    print(f"  {fpath}: {jwts[:3]}")
                # Also search in files we've been creating - look for jwt, token, accessToken
                tokens = re.findall(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', content)
                if tokens:
                    print(f"  TOKEN in {fpath}: {tokens[:3]}")
            except:
                pass

# Also check environment files
for env_file in ['tpe_service119_live.env', 'tpe119_evidence/tpe119_poc.md']:
    fpath = f'/mnt/c/Users/Administrator/desktop/JySecAI/{env_file}'
    if os.path.exists(fpath):
        with open(fpath, 'r', errors='replace') as f:
            content = f.read()
        jwts = re.findall(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', content)
        if jwts:
            print(f"  JWT in {env_file}: {jwts[:5]}")
