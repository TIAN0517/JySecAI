#!/usr/bin/env python3
"""
Direct ZoomEye AI API search for Taiwan EPCR systems
"""

import requests
import json
import warnings

warnings.filterwarnings("ignore")

# ZoomEye AI API
API_KEY = "0F4f3724-F434-7741d-D7F9-A720f2316E7"
headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "API-KEY": API_KEY
}

# S5 Proxy (if needed for ZoomEye AI API)
proxies = {
    "http": "socks5h://202.160.76.155:11084",
    "https": "socks5h://202.160.76.155:11084"
}

search_queries = [
    "title:epcr AND country:TW",
    "app:epcr AND country:TW",
    "119 AND dispatch AND country:TW"
]

# Try both with and without proxy
for use_proxy in [True, False]:
    proxy_label = "WITH" if use_proxy else "WITHOUT"
    print(f"\n=== Attempting search {proxy_label} proxy ===")
    
    for query in search_queries:
        print(f"\nSearching: {query}")
        try:
            # ZoomEye AI search API
            url = "https://api.zoomeye.ai/v2/search"
            params = {"q": query, "page": 1, "per_page": 20}
            
            proxy_setting = proxies if use_proxy else None
            
            resp = requests.get(url, headers=headers, params=params, 
                              proxies=proxy_setting, verify=False, timeout=30)
            
            print(f"  Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("data", []) or data.get("results", [])
                print(f"  Results found: {len(results) if results else 'N/A'}")
                
                if results:
                    with open(f"zoomeye_results_{query.replace(':', '_').replace(' ', '_')[:50]}.json", "w") as f:
                        json.dump(data, f, indent=2)
                    print("  Results saved to JSON")
                    
                    for item in results[:5]:
                        ip = item.get("ip", "")
                        port = item.get("port", "")
                        title = item.get("title", "")
                        host = item.get("host", "")
                        print(f"    - {ip}:{port} | {title}")
            else:
                print(f"  Response: {resp.text[:200]}")
                
        except Exception as e:
            print(f"  Error: {e}")