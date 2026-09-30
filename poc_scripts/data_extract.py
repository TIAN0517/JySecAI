#!/usr/bin/env python3
"""
Check if user endpoints return actual data or just default HTML
"""

import requests
import re
import json

TARGET = "https://210.69.42.55"
sess = requests.Session()
sess.verify = False

print("=" * 60)
print("Data Extraction Test - User Endpoints")
print("=" * 60)

# Test if we can get actual user data
endpoints = [
    "/user/1",
    "/users/1",
    "/api/users/1",
    "/user/admin",
    "/user/root",
    "/user/test",
    "/user/demo",
    "/user/0",
    "/user/999999"
]

for endpoint in endpoints:
    r = sess.get(f"{TARGET}{endpoint}")
    
    # Check if content is different from default login page
    has_form = "<form" in r.text
    has_login = "login" in r.text.lower()
    has_user_content = "user" in r.text.lower() and "table" in r.text.lower()  # HTML table = data table
    
    # Check for JSON response
    try:
        data = r.json()
        is_json = True
    except:
        is_json = False
    
    # Check content length
    content_len = len(r.text)
    
    # Check for actual data indicators
    data_indicators = []
    if "table" in r.text or "row" in r.text or "<td>" in r.text:
        data_indicators.append("table_tags")
    if "id" in r.text and "name" in r.text and "admin" in r.text:
        data_indicators.append("user_fields")
    if re.search(r'\d{3}\s*\d{4}', r.text):  # ID format like 123 4567
        data_indicators.append("id_format")
    
    print(f"\n{endpoint}:")
    print(f"  Status: {r.status_code}")
    print(f"  JSON: {is_json}")
    print(f"  Length: {content_len}")
    print(f"  Has form: {has_form}")
    print(f"  Data indicators: {data_indicators if data_indicators else 'None'}")
    
    if is_json:
        print(f"  JSON preview: {r.text[:200]}")
    elif data_indicators:
        # Extract table content
        tables = re.findall(r'<table.*?</table>', r.text, re.DOTALL)
        if tables:
            print(f"  Table found, rows: {tables[0].count('<tr>')}")