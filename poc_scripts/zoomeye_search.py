#!/usr/bin/env python3
"""
Use Zoomeye to search for government emergency systems
"""

import requests
import json

sess = requests.Session()
sess.verify = False

# Try Zoomeye API for government emergency systems
zoomeye_api = "https://api.zoomeye.org/v2/search"

queries = [
    # Taipei emergency APIs
    'title:"臺北市政府消防局" AND component:"apache" AND port:443',
    'title:"消防局" AND "119" AND country:"TW"',
    'http.title:"臺北市" AND "緊急" AND "dispatch"',
    
    # Kaohsiung emergency
    '"高雄市政府" AND "消防" AND "119"',
    '"kaohsiung" AND "fire" AND "dispatch"',
    
    # Taoyuan emergency
    '"桃園市政府" AND "消防" AND "119"',
    '"taoyuan" AND "fire" AND "emergency"',
    
    # New Taipei / ePCR
    '"epcr" AND country:"TW"',
    '"救護車" AND country:"TW"',
    '"急救" AND "119" AND "系統"',
    
    # General emergency dispatch systems
    '"emergency dispatch" AND country:"TW"',
    '"112" AND "emergency" AND "taiwan"',
]

print("=== Zoomeye 搜尋政府緊急系統 ===\n")

for query in queries:
    try:
        r = sess.get(f"https://www.zoomeye.org/search?q={requests.utils.quote(query)}", timeout=20)
        print(f"Query: {query}")
        print(f"Status: {r.status_code}")
        
        # Extract results
        results = re.findall(r'href="https://([^"]+)"', r.text)
        unique_results = list(set(results))[:5]
        for res in unique_results:
            print(f"  Found: https://{res}")
        
        # Also check for IP addresses
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', r.text)
        if ips:
            unique_ips = list(set(ips))[:5]
            print(f"  IPs found: {unique_ips}")
            
    except Exception as e:
        print(f"Query: {query}")
        print(f"  Error: {str(e)[:60]}")
    
    print()

# Try direct Zoomeye API if available
print("=== Trying Zoomeye API directly ===")
try:
    api_queries = [
        "epcr.gov.tw",
        "emergency.119.gov.tw", 
        "dispatch.119.gov.tw",
        "fire.taiwan.gov.tw",
        "119.taipei.gov.tw"
    ]
    
    for q in api_queries:
        r = sess.get(f"https://api.zoomeye.org/v1/search/hostname?q={q}", timeout=10)
        print(f"{q}: {r.status_code}")
        if r.status_code == 200:
            try:
                data = r.json()
                print(json.dumps(data, indent=2)[:500])
            except:
                print(r.text[:300])
        print()
except Exception as e:
    print(f"API test failed: {e}")

import re