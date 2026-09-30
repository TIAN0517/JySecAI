#!/usr/bin/env python3
"""
Search for Taipei, Kaohsiung, Taoyuan government emergency domains
"""

import requests

sess = requests.Session()
sess.verify = False

# Comprehensive list of government domains for these cities
domains = [
    # Taipei City - 政府相關
    'www.tp.gov.tw',
    'gov.taipei',
    '119.taipei.gov.tw',
    'fire.tp.gov.tw',
    'disaster.tp.gov.tw',
    'dispatch.tp.gov.tw',
    'emergency.tp.gov.tw',
    'api.tp.gov.tw',
    'opendata.tp.gov.tw',
    'ef.tp.gov.tw',
    'www.dff.org.tw',
    
    # Kaohsiung City - 高雄市政府
    'www.khh.gov.tw',
    'disaster.khh.gov.tw',
    'fire.khh.gov.tw',
    '119.khh.gov.tw',
    'dispatch.khh.gov.tw',
    'emergency.khh.gov.tw',
    'api.khh.gov.tw',
    
    # Taoyuan City - 桃園市政府
    'www.ty.gov.tw',
    'ty.gov.tw',
    'disaster.ty.gov.tw',
    'fire.ty.gov.tw',
    '119.ty.gov.tw',
    'dispatch.ty.gov.tw',
    'emergency.ty.gov.tw',
    'api.ty.gov.tw',
    
    # New Taipei City - 新北市 (epcr所在)
    'www.np.gov.tw',
    'epcr.np.gov.tw',
    'disaster.np.gov.tw',
    'fire.np.gov.tw',
    '119.np.gov.tw',
    'dispatch.np.gov.tw',
    'emergency.np.gov.tw',
    
    # Central Taiwan - 中部
    'www.taoyuan.gov.tw',
    'www.ttc.gov.tw',
    
    # Taiwan government agencies
    'www.119.gov.tw',
    'www.af-search.119.gov.taipei',
    '119service.119.gov.tw',
    'emergency.119.gov.tw',
    'dispatch.119.gov.tw',
    
    # Disaster/Emergency services
    'disaster.gov.tw',
    'jtwra.ncd.com.tw',
    'disaster.earth.tw',
]

print("=== 逐一驗證域名存取狀態 ===\n")

for domain in domains:
    try:
        # Try HTTPS first
        url = f"https://{domain}"
        r = sess.get(url, timeout=10, allow_redirects=True)
        status = "✓"
        info = f"{r.status_code} ({len(r.text)} bytes)"
        if r.status_code == 200:
            # Extract title
            import re
            title_match = re.search(r'<title>([^<]+)</title>', r.text)
            if title_match:
                title = title_match.group(1).strip()[:30]
                info += f" - {title}"
    except Exception as e:
        url = f"http://{domain}"
        try:
            r = sess.get(url, timeout=10, allow_redirects=True)
            status = "✓"
            info = f"{r.status_code} ({len(r.text)} bytes - HTTP)"
        except:
            status = "✗"
            info = f"ERROR: {str(e)[:40]}"
    
    print(f"{status} https://{domain}")
    print(f"    {info}")