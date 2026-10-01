#!/usr/bin/env python3
"""Print raw 3800 socket.io handshake response to diagnose SID extraction."""
import requests, urllib3, json, re, urllib.parse
urllib3.disable_warnings()
s = requests.Session()
r = s.get("http://35.234.50.28:3800/socket.io/?EIO=4&transport=polling", timeout=10)
print("=== HEADERS ===")
for k,v in r.headers.items():
    print(f"  {k}: {v}")
print("=== BODY ===")
print(repr(r.text[:800]))
print("=== LENGTH ===", len(r.text))
# Try parse sid
m = re.search(r'"sid":"([^"]+)"', r.text)
print("=== SID via regex ===", m.group(1) if m else None)
# Drain
print("\n=== DRAIN POLLING ===")
m_url = f"http://35.234.50.28:3800/socket.io/?EIO=4&transport=polling&sid={m.group(1)}"
r2 = s.get(m_url, timeout=10)
print("drain headers:", dict(r2.headers))
print("drain body:", repr(r2.text[:400]))
