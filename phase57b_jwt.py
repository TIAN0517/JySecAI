#!/usr/bin/env python3
"""Phase 57b: Quick JWT search in specific files."""
import re

# Files most likely to contain JWTs from EPCR
files_to_check = [
    '/mnt/c/Users/Administrator/desktop/JySecAI/tpe_service119_live.env',
    '/mnt/c/Users/Administrator/desktop/JySecAI/evidence/epcr_reverse_engineering.json',
    '/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/tpe119_poc.md',
    '/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/地毯搜索_119登入口報告.md',
    '/mnt/c/Users/Administrator/desktop/JySecAI/phase26_jwt_fsm.py',
    '/mnt/c/Users/Administrator/desktop/JySecAI/phase25_output.txt',
    '/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/http_targets/',
]

print("=== Searching for JWTs ===")
found = False
for fpath in files_to_check:
    try:
        with open(fpath, 'r', errors='replace') as f:
            content = f.read()
        jwts = re.findall(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', content)
        if jwts:
            found = True
            print(f"\n{fpath}:")
            for jwt in jwts[:5]:
                print(f"  JWT: {jwt[:100]}...")
        
        # Also look for "token", "accessToken", "Capapikey", "jwt"
        tokens = re.findall(r'(?:token|accessToken|Capapikey|jwt)["\s:=]+(["\'])(eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)\1', content, re.I)
        if tokens:
            for t in tokens[:5]:
                print(f"  {t[0]}: {t[1][:100]}...")
    except Exception as e:
        pass

if not found:
    print("No JWTs found in the searched files.")
    # Let's look at what we stored in JWT-related files
    print("\n=== Checking phase26_jwt_fsm.py for stored JWT info ===")
    try:
        with open('/mnt/c/Users/Administrator/desktop/JySecAI/phase26_jwt_fsm.py', 'r') as f:
            print(f.read()[:2000])
    except Exception as e:
        print(f"Error: {e}")
