#!/usr/bin/env python3
"""
Direct ZoomEye AI API search (POST) for Taiwan EPCR systems
"""

import requests
import json
import warnings

warnings.filterwarnings("ignore")

API_KEY = "0F4f3724-F434-7741d-D7F9-A720f2316E7"
headers = {
    "Content-Type": "application/json",
    "API-KEY": API_KEY,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

proxies = {
    "http": "socks5h://202.160.76.155:11084",
    "https": "socks5h://202.160.76.155:11084"
}

search_queries = [
    "title:epcr AND country:TW",
    "app:epcr AND country:TW",
    "119 AND dispatch AND country:TW"
]

# Try POST without proxy first
for query in search_queries:
    print(f"\nSearching: {query}")
    try:
        url = "https://api.zoomeye.ai/v2/search"
        payload = {"q": query, "page": 1, "per_page": 20}
        
        resp = requests.post(url, headers=headers, json=payload,
                           proxies=None, verify=False, timeout=30)
        
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("data", []) or data.get("results", [])
            print(f"  Results: {len(results) if results else 'N/A'}")
            
            if results:
                filename = query.replace(':', '_').replace(' ', '_')[:40]
                with open(f"zoomeye_results_{filename}.json", "w") as f:
                    json.dump(data, f, indent=2)
                print(f"  Saved: zoomeye_results_{filename}.json")
                
                for item in results[:10]:
                    ip = item.get("ip", "")
                    port = item.get("port", "")
                    title = item.get("title", "")
                    host = item.get("host", "")
                    print(f"    - {ip}:{port} | {title[:40]}")
        else:
            print(f"  Error: {resp.text[:300]}")
            
    except Exception as e:
        print(f"  Exception: {e}")