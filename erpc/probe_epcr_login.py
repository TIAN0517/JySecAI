import requests, urllib3, json, time
urllib3.disable_warnings()

base = "https://epcr.tpf.gov.tw:4004"

# Try login with different field names and formats
print("=== EPCR 4004 /login attempts ===")

# Try with form data
for data in [
    {"username": "admin", "password": "admin"},
    {"username": "admin", "password": "admin123"},
    {"acc": "admin", "pw": "admin"},
    {"account": "admin", "password": "admin123"},
    {"account_name": "admin", "password": "admin123"},
    {"email": "admin@tpe.gov.tw", "password": "admin123"},
]:
    try:
        r = requests.post(f"{base}/login", data=data, verify=False, timeout=10)
        body = r.text[:150]
        print(f"  form {data} -> {r.status_code}: {body}")
    except Exception as e:
        print(f"  form {data} -> ERROR: {e}")

# Try with JSON
for data in [
    {"username": "admin", "password": "admin"},
    {"username": "admin", "password": "admin123"},
    {"acc": "admin", "pw": "admin"},
    {"account": "admin", "password": "admin123"},
    {"account_name": "admin", "password": "admin123"},
]:
    try:
        r = requests.post(f"{base}/login", json=data, verify=False, timeout=10)
        body = r.text[:150]
        print(f"  json {data} -> {r.status_code}: {body}")
    except Exception as e:
        print(f"  json {data} -> ERROR: {e}")

# Try the tokens.json for existing refresh token
print("\n=== Existing tokens ===")
try:
    with open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/tokens.json") as f:
        t = json.load(f)
        print(json.dumps(t, indent=2))
except:
    print("No tokens.json")

# Try refreshToken with different values
print("\n=== /refreshToken with various values ===")
for rt in ["", "test", "eyJhbG", "femet"]:
    r = requests.post(f"{base}/refreshToken", json={"refreshToken": rt}, verify=False, timeout=10)
    print(f"  rt={rt} -> {r.status_code}: {r.text[:150]}")

# Try ssoLogin
print("\n=== /ssoLogin ===")
for data in [{"sessionId": "test"}, {"session_id": "test"}]:
    r = requests.post(f"{base}/ssoLogin", json=data, verify=False, timeout=10)
    print(f"  {data} -> {r.status_code}: {r.text[:150]}")
